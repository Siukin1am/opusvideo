from __future__ import annotations

from ..schemas import AdvisorNotes, Brief, Decision, Evaluation, Pitch, PitchDeck, Script
from .base import Role, dump


class Writer(Role):
    name = "Writer"
    persona = """You are the head writer. You write tight, visual, performable sketch comedy.
Every scene needs a clear game (the unusual thing), heightening, and a button. Dialogue is short
and speakable; favour visual jokes because the final medium is video with short AI clips.
Keep the cast to at most 3 characters and locations to at most 3 so it stays producible."""

    def pitch(self, brief: Brief, n: int) -> PitchDeck:
        return self.ask(
            f"Brief:\n{dump(brief)}\n\nPitch {n} distinctly different sketch concepts for this brief.",
            PitchDeck,
        )

    def draft(self, brief: Brief, pitch: Pitch, directives: list[str]) -> Script:
        return self.ask(
            f"Brief:\n{dump(brief)}\n\nApproved pitch:\n{dump(pitch)}\n\n"
            f"Producer directives:\n- " + "\n- ".join(directives or ["none"]) + "\n\n"
            f"Write the full script. Target runtime about {brief.duration_sec} seconds "
            "(roughly 2-3 short lines per 10 seconds). Use scene ids S1, S2, ...",
            Script,
        )

    def revise(self, brief: Brief, script: Script, notes: AdvisorNotes,
               evaluation: Evaluation, decision: Decision) -> Script:
        return self.ask(
            f"Brief:\n{dump(brief)}\n\nCurrent draft:\n{dump(script)}\n\n"
            f"Comedy advisor notes:\n{dump(notes)}\n\nExaminer evaluation:\n{dump(evaluation)}\n\n"
            f"Chief decider verdict and directives:\n{dump(decision)}\n\n"
            "Write the next draft. Apply the directives first, then the critical and major notes. "
            "Keep what works. Keep scene ids stable where scenes survive.",
            Script,
        )
