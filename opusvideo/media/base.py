"""Media provider interface: the Photo Generator and Video Generator crew members."""

from __future__ import annotations

from pathlib import Path
from typing import Protocol, Sequence


class MediaProvider(Protocol):
    def generate_image(self, prompt: str, out_path: Path, *, negative_prompt: str = "",
                       references: Sequence[Path] = (), aspect_ratio: str = "16:9") -> Path: ...

    def generate_video(self, prompt: str, start_image: Path, out_path: Path, *,
                       duration_sec: int = 5, negative_prompt: str = "",
                       aspect_ratio: str = "16:9") -> Path: ...
