"""Thin wrapper around the Anthropic SDK used by every Claude-backed role."""

from __future__ import annotations

import base64
import logging
from pathlib import Path
from typing import Protocol, Sequence, TypeVar

import anthropic
from pydantic import BaseModel

from .config import Settings

log = logging.getLogger(__name__)

T = TypeVar("T", bound=BaseModel)

# Server-side fallback: if a classifier declines, the API retries on Anthropic's
# recommended model for that refusal category inside the same call.
FALLBACK_BETA = "server-side-fallback-2026-07-01"


class RoleRefused(RuntimeError):
    """Raised when Claude (and its fallback) declined the request."""


class LLM(Protocol):
    def structured(
        self,
        *,
        role: str,
        system: str,
        prompt: str,
        schema: type[T],
        effort: str | None = None,
        images: Sequence[Path] = (),
    ) -> T: ...


def _image_block(path: Path) -> dict:
    media_type = {".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg",
                  ".webp": "image/webp"}.get(path.suffix.lower(), "image/png")
    data = base64.standard_b64encode(path.read_bytes()).decode("utf-8")
    return {"type": "image", "source": {"type": "base64", "media_type": media_type, "data": data}}


class ClaudeLLM:
    def __init__(self, settings: Settings, client: anthropic.Anthropic | None = None):
        self.settings = settings
        self.client = client or anthropic.Anthropic()

    def structured(
        self,
        *,
        role: str,
        system: str,
        prompt: str,
        schema: type[T],
        effort: str | None = None,
        images: Sequence[Path] = (),
    ) -> T:
        content: list[dict] = [_image_block(Path(p)) for p in images]
        content.append({"type": "text", "text": prompt})

        log.info("[%s] calling %s (effort=%s)", role, self.settings.model,
                 effort or self.settings.writing_effort)
        try:
            response = self.client.messages.parse(
                model=self.settings.model,
                max_tokens=self.settings.max_tokens,
                system=system,
                messages=[{"role": "user", "content": content}],
                thinking={"type": "adaptive"},
                output_config={"effort": effort or self.settings.writing_effort},
                output_format=schema,
                extra_headers={"anthropic-beta": FALLBACK_BETA},
                extra_body={"fallbacks": "default"},
            )
        except anthropic.RateLimitError:
            log.error("[%s] rate limited after SDK retries", role)
            raise
        except anthropic.APIStatusError as e:
            log.error("[%s] API error %s (request %s): %s", role, e.status_code,
                      e.response.headers.get("request-id"), e.message)
            raise

        if response.stop_reason == "refusal":
            category = response.stop_details.category if response.stop_details else None
            raise RoleRefused(f"{role} request was declined (category={category})")
        if response.stop_reason == "max_tokens":
            raise RuntimeError(f"{role} output hit max_tokens={self.settings.max_tokens}")
        if response.parsed_output is None:
            raise RuntimeError(f"{role} returned no parseable output")

        usage = response.usage
        log.info("[%s] done: %s in / %s out tokens", role, usage.input_tokens, usage.output_tokens)
        return response.parsed_output
