"""Command line entry point: `opusvideo "a premise"`."""

from __future__ import annotations

import argparse
import logging
from pathlib import Path

from .config import Settings
from .llm import ClaudeLLM
from .media import get_provider
from .pipeline import Studio, slug
from .schemas import Brief
from .store import RunStore


def main(argv: list[str] | None = None) -> None:
    p = argparse.ArgumentParser(prog="opusvideo", description="Make a short comedy video with an AI crew.")
    p.add_argument("premise", help="One-line premise for the sketch")
    p.add_argument("--run-id", help="Resume or name a run (default: slug of the premise)")
    p.add_argument("--duration", type=int, default=60, help="Target runtime in seconds")
    p.add_argument("--tone", default="playful, absurd, warm")
    p.add_argument("--audience", default="general adult audience")
    p.add_argument("--style", default="live-action sitcom look, bright natural lighting")
    p.add_argument("--language", default="English")
    p.add_argument("--media", choices=["mock", "replicate"], help="Image/video provider (default: $OPUSVIDEO_MEDIA or mock)")
    p.add_argument("--aspect", choices=["16:9", "9:16", "1:1"])
    p.add_argument("--max-rounds", type=int, help="Max script revision rounds")
    p.add_argument("--max-shots", type=int)
    p.add_argument("--stop-after", choices=["script", "plan", "keyframes"],
                   help="Stop early to review before paying for media")
    p.add_argument("-v", "--verbose", action="store_true")
    a = p.parse_args(argv)

    logging.basicConfig(level=logging.DEBUG if a.verbose else logging.INFO,
                        format="%(asctime)s %(levelname)s %(name)s: %(message)s")
    for noisy in ("httpx", "httpx2", "anthropic", "urllib3"):
        logging.getLogger(noisy).setLevel(logging.WARNING)

    s = Settings()
    if a.media:
        s.media_provider = a.media
    if a.aspect:
        s.aspect_ratio = a.aspect
    if a.max_rounds:
        s.max_script_rounds = a.max_rounds
    if a.max_shots:
        s.max_shots = a.max_shots

    brief = Brief(premise=a.premise, audience=a.audience, tone=a.tone,
                  duration_sec=a.duration, style=a.style, language=a.language)
    store = RunStore(Path(s.runs_dir) / (a.run_id or slug(a.premise)))
    studio = Studio(s, ClaudeLLM(s), get_provider(s), store)
    out = studio.run(brief, stop_after=a.stop_after)
    print(out or f"Stopped after {a.stop_after}; artifacts in {store.root}")


if __name__ == "__main__":
    main()
