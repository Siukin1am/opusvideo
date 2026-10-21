"""The studio: orchestrates the crew from premise to final cut."""

from __future__ import annotations

import logging
import re
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from pathlib import Path

from .config import Settings
from .llm import LLM
from .media import MediaProvider
from .media.editor import assemble
from .roles import (Actor, Advisor, ChiefDecider, Director, Examiner, PromptEngineer,
                    RoleCreator, Writer)
from .schemas import (AdvisorNotes, Brief, Cast, Decision, Evaluation, FinalReview,
                      KeyframeReview, Performance, PitchChoice, PitchDeck, PromptBook, Script,
                      ShotList)
from .store import RunStore

log = logging.getLogger(__name__)


class ScriptKilled(RuntimeError):
    pass


@dataclass
class RoomRound:
    script: Script
    notes: AdvisorNotes
    evaluation: Evaluation
    decision: Decision


def slug(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")[:40] or "run"


class Studio:
    def __init__(self, settings: Settings, llm: LLM, media: MediaProvider, store: RunStore):
        self.s = settings
        self.media = media
        self.store = store
        self.writer = Writer(llm, settings)
        self.advisor = Advisor(llm, settings)
        self.examiner = Examiner(llm, settings)
        self.chief = ChiefDecider(llm, settings)
        self.casting = RoleCreator(llm, settings)
        self.director = Director(llm, settings)
        self.actor = Actor(llm, settings)
        self.prompter = PromptEngineer(llm, settings)

    # ---------- pre-production: words ----------

    def writers_room(self, brief: Brief) -> Script:
        st = self.store
        deck = st.stage("01_pitches", PitchDeck, lambda: self.writer.pitch(brief, self.s.pitches))
        choice = st.stage("02_pitch_choice", PitchChoice, lambda: self.chief.choose_pitch(brief, deck))
        pitch = deck.pitches[max(0, min(choice.chosen_index, len(deck.pitches) - 1))]
        log.info("Chief picked: %s", pitch.title)

        script = st.stage("03_draft_1", Script, lambda: self.writer.draft(brief, pitch, choice.directives))
        for rnd in range(1, self.s.max_script_rounds + 1):
            notes = st.stage(f"03_draft_{rnd}_notes", AdvisorNotes,
                             lambda: self.advisor.review(brief, script))
            evaluation = st.stage(f"03_draft_{rnd}_eval", Evaluation,
                                  lambda: self.examiner.evaluate_script(brief, script))
            decision = st.stage(f"03_draft_{rnd}_decision", Decision,
                                lambda: self.chief.decide(brief, script, notes, evaluation,
                                                          rnd, self.s.max_script_rounds))
            log.info("Draft %d: examiner %d/10, chief says %s", rnd, evaluation.overall, decision.verdict)
            if decision.verdict == "approve":
                break
            if decision.verdict == "kill":
                raise ScriptKilled(decision.rationale)
            if rnd == self.s.max_script_rounds:
                log.warning("Out of rounds; shooting draft %d despite verdict %s", rnd, decision.verdict)
                break
            prev = script
            script = st.stage(f"03_draft_{rnd + 1}", Script,
                              lambda: self.writer.revise(brief, prev, notes, evaluation, decision))
        st.save("04_script_final", script)
        return script

    # ---------- pre-production: people & plan ----------

    def plan(self, brief: Brief, script: Script) -> tuple[Cast, ShotList, PromptBook]:
        st = self.store
        cast = st.stage("05_cast", Cast, lambda: self.casting.cast(brief, script))
        shots = st.stage("06_shot_list", ShotList,
                         lambda: self.director.shoot(brief, script, cast, self.s.max_shots))

        def perform_all() -> list[Performance]:
            with ThreadPoolExecutor(self.s.parallelism) as pool:
                return list(pool.map(lambda c: self.actor.perform(c, shots), cast.characters))

        performances = st.stage("07_performances", list[Performance], perform_all)
        prompts = st.stage("08_prompt_book", PromptBook,
                           lambda: self.prompter.write(brief, cast, shots, performances))
        return cast, shots, prompts

    # ---------- production: pixels ----------

    def character_refs(self, cast: Cast, prompts: PromptBook) -> dict[str, Path]:
        def render(c):
            out = self.store.path("refs", f"{slug(c.name)}.png")
            if not out.exists():
                self.media.generate_image(
                    f"{prompts.style_prefix} Character reference portrait, front-facing, neutral "
                    f"background, waist-up. {c.visual_bible}", out, aspect_ratio="1:1")
            return c.name, out

        with ThreadPoolExecutor(self.s.parallelism) as pool:
            return dict(pool.map(render, cast.characters))

    def keyframes(self, cast: Cast, shots: ShotList, prompts: PromptBook,
                  refs: dict[str, Path]) -> tuple[dict[str, Path], list[KeyframeReview]]:
        by_id = {s.shot_id: s for s in shots.all_shots()}

        def shoot(sp):
            shot = by_id.get(sp.shot_id)
            shot_refs = [refs[n] for n in (shot.characters if shot else []) if n in refs]
            prompt = f"{prompts.style_prefix} {sp.image_prompt}"
            review = None
            for attempt in range(self.s.max_keyframe_retries + 1):
                out = self.store.path("keyframes", f"{sp.shot_id}_v{attempt}.png")
                if not out.exists():
                    self.media.generate_image(prompt, out, negative_prompt=sp.negative_prompt,
                                              references=shot_refs, aspect_ratio=self.s.aspect_ratio)
                review = self.store.stage(
                    f"09_qa/{sp.shot_id}_v{attempt}", KeyframeReview,
                    lambda: self.examiner.review_keyframe(sp, cast, out,
                                                          {n: refs[n] for n in refs if refs[n] in shot_refs}))
                if not review.regenerate:
                    break
                prompt = self.prompter.fix(prompt, review.prompt_fix)
            return sp.shot_id, out, review

        with ThreadPoolExecutor(self.s.parallelism) as pool:
            results = list(pool.map(shoot, prompts.prompts))
        return {sid: path for sid, path, _ in results}, [r for _, _, r in results]

    def clips(self, shots: ShotList, prompts: PromptBook, frames: dict[str, Path]) -> list[Path]:
        by_id = {p.shot_id: p for p in prompts.prompts}

        def animate(shot):
            sp = by_id[shot.shot_id]
            out = self.store.path("clips", f"{shot.shot_id}.mp4")
            if not out.exists():
                self.media.generate_video(sp.video_prompt, frames[shot.shot_id], out,
                                          duration_sec=max(3, min(shot.duration_sec, 10)),
                                          negative_prompt=sp.negative_prompt,
                                          aspect_ratio=self.s.aspect_ratio)
            return out

        ordered = [s for s in shots.all_shots() if s.shot_id in by_id and s.shot_id in frames]
        with ThreadPoolExecutor(self.s.parallelism) as pool:
            return list(pool.map(animate, ordered))

    # ---------- the whole show ----------

    def run(self, brief: Brief, *, stop_after: str | None = None) -> Path | None:
        self.store.save("00_brief", brief)
        script = self.writers_room(brief)
        if stop_after == "script":
            return None
        cast, shots, prompts = self.plan(brief, script)
        if stop_after == "plan":
            return None

        refs = self.character_refs(cast, prompts)
        frames, reviews = self.keyframes(cast, shots, prompts, refs)
        qa = "\n".join(f"{r.shot_id}: {r.score}/10 {'; '.join(r.issues) or 'ok'}" for r in reviews)
        final = self.store.stage("10_final_review", FinalReview,
                                 lambda: self.chief.final_review(brief, script, shots, prompts, qa))
        if final.verdict == "reshoot":
            log.warning("Chief wants reshoots of %s: %s", final.reshoot_shot_ids, final.rationale)
        if stop_after == "keyframes":
            return None

        ordered_shots = [s for s in shots.all_shots() if s.shot_id in frames]
        clips = self.clips(shots, prompts, frames)
        out = assemble(clips, ordered_shots, self.store.path("final.mp4"), self.s.aspect_ratio)
        log.info("Final cut: %s", out)
        return out
