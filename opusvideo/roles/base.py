"""Shared plumbing for Claude-backed crew members."""

from __future__ import annotations

import json
from typing import Sequence, TypeVar

from pydantic import BaseModel

from ..config import Settings
from ..llm import LLM

T = TypeVar("T", bound=BaseModel)

HOUSE_STYLE = """You work at a small comedy studio that makes short AI-generated sketch videos.
House rules: jokes punch up, never down; no real private individuals; no sexual content
involving minors; keep it broadcast-safe (PG-13). Comedy comes from character, specificity,
escalation and timing, not from randomness alone."""


def dump(*objs: BaseModel | Sequence[BaseModel]) -> str:
    """Render role outputs as JSON for the next role's prompt."""
    def plain(o):
        if isinstance(o, BaseModel):
            return o.model_dump()
        return [plain(x) for x in o]
    return "\n\n".join(json.dumps(plain(o), indent=2, ensure_ascii=False) for o in objs)


class Role:
    name: str = "role"
    persona: str = ""
    judging: bool = False

    def __init__(self, llm: LLM, settings: Settings):
        self.llm = llm
        self.settings = settings

    @property
    def system(self) -> str:
        return f"{HOUSE_STYLE}\n\nYour role: {self.name}.\n{self.persona}"

    def ask(self, prompt: str, schema: type[T], images=()) -> T:
        effort = self.settings.judging_effort if self.judging else self.settings.writing_effort
        return self.llm.structured(role=self.name, system=self.system, prompt=prompt,
                                   schema=schema, effort=effort, images=images)
