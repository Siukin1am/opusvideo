from __future__ import annotations

from ..schemas import (AdvisorNotes, Brief, Decision, Evaluation, FinalReview, PitchChoice,
                       PitchDeck, PromptBook, Script, ShotList)
from .base import Role, dump


class ChiefDecider(Role):
    name = "Chief Decider"
    judging = True
    persona = """You are the executive producer and the final decision maker. You weigh the
advisor's taste and the examiner's scores, then make a clear call. You protect the budget:
approve when the script is genuinely good enough to shoot, ask for revisions with a short list
of concrete directives when it is close, and kill it only when the concept is unfixable."""

    def choose_pitch(self, brief: Brief, deck: PitchDeck) -> PitchChoice:
        return self.ask(f"Brief:\n{dump(brief)}\n\nPitches:\n{dump(deck)}\n\n"
                        "Pick the pitch to develop and give the writer directives.", PitchChoice)

    def decide(self, brief: Brief, script: Script, notes: AdvisorNotes, evaluation: Evaluation,
               round_no: int, max_rounds: int) -> Decision:
        return self.ask(
            f"Brief:\n{dump(brief)}\n\nDraft {round_no} of at most {max_rounds}:\n{dump(script)}\n\n"
            f"Advisor notes:\n{dump(notes)}\n\nExaminer evaluation:\n{dump(evaluation)}\n\n"
            "Make the call. On the last allowed round, approve unless the script is unshootable.",
            Decision,
        )

    def final_review(self, brief: Brief, script: Script, shots: ShotList, prompts: PromptBook,
                     qa_summary: str) -> FinalReview:
        return self.ask(
            f"Brief:\n{dump(brief)}\n\nScript:\n{dump(script)}\n\nShot list:\n{dump(shots)}\n\n"
            f"Prompt book:\n{dump(prompts)}\n\nKeyframe QA summary:\n{qa_summary}\n\n"
            "Decide whether to ship the cut or reshoot specific shots.",
            FinalReview,
        )
