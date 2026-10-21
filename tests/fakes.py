"""Canned crew outputs so the whole pipeline runs offline in tests."""

from __future__ import annotations

from opusvideo.schemas import (AdvisorNotes, Cast, Character, Decision, DirectedScene, Evaluation,
                               FinalReview, KeyframeReview, Line, LineReading, Note, Performance,
                               Pitch, PitchChoice, PitchDeck, PromptBook, Score, Script, ScriptScene,
                               Shot, ShotList, ShotPrompt)

NAMES = ["Gary", "Pigeon"]


def _lines():
    return [Line(character="Gary", text="I'd like to return this pigeon."),
            Line(character="Pigeon", text="He's not my type either.", parenthetical="deadpan")]


class FakeLLM:
    def __init__(self, verdicts=("revise", "approve"), regenerate_first=True):
        self.calls: list[str] = []
        self.verdicts = list(verdicts)
        self.regenerate_first = regenerate_first
        self._reviewed: set[str] = set()

    def structured(self, *, role, system, prompt, schema, effort=None, images=()):
        self.calls.append(role)
        return getattr(self, f"_{schema.__name__}")(prompt, images)

    def _PitchDeck(self, prompt, images):
        return PitchDeck(pitches=[Pitch(title=f"Pitch {i}", logline="A man returns a pigeon.",
                                        comedic_engine="bureaucracy vs bird", beats=["a", "b"])
                                  for i in range(3)])

    def _PitchChoice(self, prompt, images):
        return PitchChoice(chosen_index=1, rationale="best", directives=["keep it short"])

    def _Script(self, prompt, images):
        return Script(title="Return Policy", logline="A man returns a pigeon.", ending_tag="Pigeon gets a refund.",
                      scenes=[ScriptScene(scene_id="S1", setting="store", summary="return",
                                          comedic_beat="deadpan bird", lines=_lines())])

    def _AdvisorNotes(self, prompt, images):
        return AdvisorNotes(overall="good", strengths=["bird"], funniest_moment="refund",
                            weakest_moment="opening",
                            notes=[Note(scene_id="S1", issue="slow", suggestion="cut", severity="major")])

    def _Evaluation(self, prompt, images):
        return Evaluation(scores=[Score(criterion="funny", score=8, comment="yes")], overall=8,
                          passed=True, blocking_issues=[])

    def _Decision(self, prompt, images):
        return Decision(verdict=self.verdicts.pop(0), rationale="ok", directives=["punch up S1"])

    def _Cast(self, prompt, images):
        return Cast(characters=[Character(name=n, role_in_story="lead", personality="dry",
                                          comedic_trait="deadpan", voice="flat", age_range="40s",
                                          visual_bible=f"{n} visual bible") for n in NAMES])

    def _ShotList(self, prompt, images):
        return ShotList(visual_style="sitcom", scenes=[DirectedScene(
            scene_id="S1", location_visual="pet store", mood="bright",
            shots=[Shot(shot_id="S1-01", duration_sec=3, shot_type="wide", camera_move="static",
                        action="Gary enters", characters=["Gary"], dialogue=_lines()[:1],
                        comedic_timing="hold"),
                   Shot(shot_id="S1-02", duration_sec=4, shot_type="close-up", camera_move="push in",
                        action="Pigeon stares", characters=["Pigeon"], dialogue=_lines()[1:],
                        comedic_timing="cut on reaction")])])

    def _Performance(self, prompt, images):
        name = next(n for n in NAMES if f"performance as {n}" in prompt)
        return Performance(character=name, acting_choices="underplay",
                           line_readings=[LineReading(shot_id="S1-01", text="...", delivery="dry",
                                                      facial_expression="blank", body_language="still")])

    def _PromptBook(self, prompt, images):
        return PromptBook(style_prefix="sitcom still.", prompts=[
            ShotPrompt(shot_id=sid, image_prompt=f"image {sid}", video_prompt=f"motion {sid}",
                       negative_prompt="text") for sid in ("S1-01", "S1-02")])

    def _KeyframeReview(self, prompt, images):
        shot_id = "S1-01" if "shot S1-01" in prompt else "S1-02"
        regen = self.regenerate_first and shot_id not in self._reviewed
        self._reviewed.add(shot_id)
        return KeyframeReview(shot_id=shot_id, characters_consistent=not regen, matches_prompt=True,
                              score=5 if regen else 9, issues=["off model"] if regen else [],
                              regenerate=regen, prompt_fix="make him taller" if regen else "")

    def _FinalReview(self, prompt, images):
        return FinalReview(verdict="ship", rationale="funny", reshoot_shot_ids=[])
