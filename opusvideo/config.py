"""Runtime configuration, read from environment variables (see .env.example)."""

from __future__ import annotations

import os
from dataclasses import dataclass, field


def _env(name: str, default: str) -> str:
    return os.environ.get(name, default)


@dataclass
class Settings:
    # Claude
    model: str = field(default_factory=lambda: _env("OPUSVIDEO_MODEL", "claude-opus-5-5"))
    writing_effort: str = field(default_factory=lambda: _env("OPUSVIDEO_WRITING_EFFORT", "high"))
    judging_effort: str = field(default_factory=lambda: _env("OPUSVIDEO_JUDGING_EFFORT", "medium"))
    max_tokens: int = 16000

    # Workflow limits
    pitches: int = 3
    max_script_rounds: int = 3
    max_keyframe_retries: int = 2
    max_shots: int = 12
    parallelism: int = 4

    # Media
    media_provider: str = field(default_factory=lambda: _env("OPUSVIDEO_MEDIA", "mock"))
    replicate_image_model: str = field(
        default_factory=lambda: _env("REPLICATE_IMAGE_MODEL", "black-forest-labs/flux-schnell")
    )
    replicate_video_model: str = field(
        default_factory=lambda: _env("REPLICATE_VIDEO_MODEL", "kwaivgi/kling-v2.1")
    )
    # Input field names differ per hosted model; override to match the model's schema.
    replicate_video_image_field: str = field(
        default_factory=lambda: _env("REPLICATE_VIDEO_IMAGE_FIELD", "start_image")
    )
    replicate_ref_image_field: str = field(
        default_factory=lambda: _env("REPLICATE_REF_IMAGE_FIELD", "")
    )
    aspect_ratio: str = field(default_factory=lambda: _env("OPUSVIDEO_ASPECT", "16:9"))

    runs_dir: str = field(default_factory=lambda: _env("OPUSVIDEO_RUNS_DIR", "runs"))
