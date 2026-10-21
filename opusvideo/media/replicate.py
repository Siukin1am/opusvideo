"""Replicate adapter: one HTTP client that can drive many hosted image and video models.

Swap models with REPLICATE_IMAGE_MODEL / REPLICATE_VIDEO_MODEL. Input field names differ per
model, so check the model's API page and set REPLICATE_VIDEO_IMAGE_FIELD (and
REPLICATE_REF_IMAGE_FIELD for image models that accept reference images) to match.
"""

from __future__ import annotations

import base64
import mimetypes
import os
import time
from pathlib import Path
from typing import Sequence

import requests

from ..config import Settings

API = "https://api.replicate.com/v1"


def _data_uri(path: Path) -> str:
    mime = mimetypes.guess_type(path.name)[0] or "image/png"
    return f"data:{mime};base64,{base64.b64encode(path.read_bytes()).decode()}"


class ReplicateProvider:
    def __init__(self, settings: Settings, token: str | None = None, poll_sec: float = 3.0,
                 timeout_sec: float = 900.0):
        self.settings = settings
        self.token = token or os.environ.get("REPLICATE_API_TOKEN")
        if not self.token:
            raise RuntimeError("REPLICATE_API_TOKEN is not set")
        self.poll_sec = poll_sec
        self.timeout_sec = timeout_sec
        self.session = requests.Session()
        self.session.headers.update({"Authorization": f"Bearer {self.token}",
                                     "Content-Type": "application/json"})

    def _run(self, model: str, inputs: dict) -> str:
        resp = self.session.post(f"{API}/models/{model}/predictions", json={"input": inputs},
                                 headers={"Prefer": "wait=60"}, timeout=120)
        resp.raise_for_status()
        pred = resp.json()
        deadline = time.monotonic() + self.timeout_sec
        while pred["status"] not in ("succeeded", "failed", "canceled"):
            if time.monotonic() > deadline:
                raise TimeoutError(f"{model} prediction {pred['id']} timed out")
            time.sleep(self.poll_sec)
            pred = self.session.get(pred["urls"]["get"], timeout=60).json()
        if pred["status"] != "succeeded":
            raise RuntimeError(f"{model} prediction {pred['status']}: {pred.get('error')}")
        output = pred["output"]
        return output[0] if isinstance(output, list) else output

    def _download(self, url: str, out_path: Path) -> Path:
        out_path.parent.mkdir(parents=True, exist_ok=True)
        with self.session.get(url, stream=True, timeout=300) as r:
            r.raise_for_status()
            with open(out_path, "wb") as f:
                for chunk in r.iter_content(1 << 16):
                    f.write(chunk)
        return out_path

    def generate_image(self, prompt: str, out_path: Path, *, negative_prompt: str = "",
                       references: Sequence[Path] = (), aspect_ratio: str = "16:9") -> Path:
        inputs: dict = {"prompt": prompt, "aspect_ratio": aspect_ratio, "output_format": "png"}
        if negative_prompt:
            inputs["negative_prompt"] = negative_prompt
        ref_field = self.settings.replicate_ref_image_field
        if ref_field and references:
            inputs[ref_field] = _data_uri(references[0])
        return self._download(self._run(self.settings.replicate_image_model, inputs), out_path)

    def generate_video(self, prompt: str, start_image: Path, out_path: Path, *,
                       duration_sec: int = 5, negative_prompt: str = "",
                       aspect_ratio: str = "16:9") -> Path:
        inputs: dict = {"prompt": prompt, "duration": duration_sec,
                        self.settings.replicate_video_image_field: _data_uri(start_image)}
        if negative_prompt:
            inputs["negative_prompt"] = negative_prompt
        return self._download(self._run(self.settings.replicate_video_model, inputs), out_path)
