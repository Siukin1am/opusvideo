"""Offline provider: draws prompt cards with Pillow and turns them into clips with ffmpeg.

Free and deterministic, for developing the script/direction stages and for tests.
"""

from __future__ import annotations

import hashlib
import subprocess
import textwrap
from pathlib import Path
from typing import Sequence

from PIL import Image, ImageDraw

SIZES = {"16:9": (1280, 720), "9:16": (720, 1280), "1:1": (1024, 1024)}


class MockProvider:
    def generate_image(self, prompt: str, out_path: Path, *, negative_prompt: str = "",
                       references: Sequence[Path] = (), aspect_ratio: str = "16:9") -> Path:
        w, h = SIZES.get(aspect_ratio, SIZES["16:9"])
        shade = int(hashlib.sha1(prompt.encode()).hexdigest()[:6], 16)
        bg = ((shade >> 16) % 128 + 64, (shade >> 8) % 128 + 64, shade % 128 + 64)
        img = Image.new("RGB", (w, h), bg)
        draw = ImageDraw.Draw(img)
        wrapped = "\n".join(textwrap.wrap(prompt, width=w // 12)[: h // 24])
        draw.multiline_text((40, 40), wrapped, fill=(255, 255, 255), spacing=6)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        img.save(out_path)
        return out_path

    def generate_video(self, prompt: str, start_image: Path, out_path: Path, *,
                       duration_sec: int = 5, negative_prompt: str = "",
                       aspect_ratio: str = "16:9") -> Path:
        out_path.parent.mkdir(parents=True, exist_ok=True)
        subprocess.run(
            ["ffmpeg", "-y", "-loglevel", "error", "-loop", "1", "-i", str(start_image),
             "-t", str(duration_sec), "-r", "24", "-vf", "zoompan=z='min(zoom+0.0015,1.2)':d=1:s="
             + "x".join(map(str, SIZES.get(aspect_ratio, SIZES["16:9"]))),
             "-pix_fmt", "yuv420p", "-c:v", "libx264", str(out_path)],
            check=True,
        )
        return out_path
