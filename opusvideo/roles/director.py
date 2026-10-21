from __future__ import annotations

from ..schemas import Brief, Cast, Script, ShotList
from .base import Role, dump


class Director(Role):
    name = "Director"
    persona = """You are the director. You turn a script into scenes and shots that AI video
models can actually render: each shot is one simple continuous action of 3-10 seconds, with at
most two characters in frame, a clear shot type and camera move. Comedy lives in timing, so
note where to hold for a beat, where to cut on the reaction, and which shot is the payoff."""

    def shoot(self, brief: Brief, script: Script, cast: Cast, max_shots: int) -> ShotList:
        return self.ask(
            f"Brief:\n{dump(brief)}\n\nScript:\n{dump(script)}\n\nCast:\n{dump(cast)}\n\n"
            f"Break it into scenes and at most {max_shots} shots in total. Shot ids look like "
            "S1-01. Assign every script line to exactly one shot's dialogue. "
            f"Total runtime about {brief.duration_sec} seconds.",
            ShotList,
        )
