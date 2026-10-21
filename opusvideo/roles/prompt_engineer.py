from __future__ import annotations

from ..schemas import Brief, Cast, Performance, PromptBook, ShotList
from .base import Role, dump


class PromptEngineer(Role):
    name = "Prompt Engineer"
    persona = """You write prompts for text-to-image and image-to-video models.
Image prompts describe one frozen keyframe: subject(s) with their full visual bible pasted
verbatim, expression, pose, location, framing, lens, lighting and the global style. Video
prompts describe only motion over the clip: what moves, how the camera moves, the facial
performance, and pacing; they must not re-describe appearance. Never put dialogue text or
captions in prompts (models garble text). Keep each prompt under 120 words."""

    def write(self, brief: Brief, cast: Cast, shots: ShotList,
              performances: list[Performance]) -> PromptBook:
        return self.ask(
            f"Global style: {brief.style}; visual style from director: {shots.visual_style}; "
            f"aspect ratio {self.settings.aspect_ratio}.\n\nCast bibles:\n{dump(cast)}\n\n"
            f"Shot list:\n{dump(shots)}\n\nPerformances:\n{dump(performances)}\n\n"
            "Write one prompt pair for every shot, using the same shot ids.",
            PromptBook,
        )

    def fix(self, prompt_text: str, fix: str) -> str:
        """Apply the examiner's fix locally; cheap and deterministic."""
        return f"{prompt_text} {fix}".strip() if fix else prompt_text
