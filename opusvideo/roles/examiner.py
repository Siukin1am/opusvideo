from __future__ import annotations

from pathlib import Path

from ..schemas import Brief, Cast, Evaluation, KeyframeReview, Script, ShotPrompt
from .base import Role, dump

RUBRIC = [
    "funny: the jokes would get real laughs",
    "clarity: the game of the scene is obvious within seconds",
    "on_brief: matches premise, tone, audience and duration",
    "producibility: few characters/locations, visual, doable as short AI video clips",
    "standards: punches up, broadcast-safe, no real private individuals",
]


class Examiner(Role):
    name = "Examiner"
    judging = True
    persona = """You are the studio's quality examiner. You are strict, fair and consistent.
You score against a fixed rubric and you fail work that has blocking problems, even if parts
are good. For images you check character consistency against the reference portraits, whether
the frame matches the shot prompt, and visible defects (extra limbs, garbled text, wrong count
of people)."""

    def evaluate_script(self, brief: Brief, script: Script, pass_mark: int = 7) -> Evaluation:
        return self.ask(
            f"Brief:\n{dump(brief)}\n\nScript:\n{dump(script)}\n\n"
            "Score each criterion 1-10:\n- " + "\n- ".join(RUBRIC) + "\n\n"
            f"Set passed=true only if overall >= {pass_mark} and there are no blocking issues.",
            Evaluation,
        )

    def review_keyframe(self, shot: ShotPrompt, cast: Cast, keyframe: Path,
                        references: dict[str, Path]) -> KeyframeReview:
        names = [c.name for c in cast.characters if c.name in references]
        images = [references[n] for n in names] + [keyframe]
        legend = "\n".join(f"Image {i + 1}: reference portrait of {n}" for i, n in enumerate(names))
        legend += f"\nImage {len(images)}: the keyframe under review"
        return self.ask(
            f"{legend}\n\nCharacter bibles:\n{dump(cast)}\n\nShot prompt:\n{dump(shot)}\n\n"
            f"Review the keyframe for shot {shot.shot_id}. Request regeneration only for problems "
            "a viewer would notice.",
            KeyframeReview,
            images=images,
        )
