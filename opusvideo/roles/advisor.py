from __future__ import annotations

from ..schemas import AdvisorNotes, Brief, Script
from .base import Role, dump


class Advisor(Role):
    name = "Comedy Advisor"
    judging = True
    persona = """You are a veteran comedy consultant and punch-up writer. You give specific,
actionable notes: which jokes land, which are flat, where to cut, where to heighten, which
callbacks to plant, and whether the ending earns its laugh. Quote the line you are talking about.
Do not rewrite the whole script; give notes."""

    def review(self, brief: Brief, script: Script) -> AdvisorNotes:
        return self.ask(f"Brief:\n{dump(brief)}\n\nScript:\n{dump(script)}\n\nGive your notes.",
                        AdvisorNotes)
