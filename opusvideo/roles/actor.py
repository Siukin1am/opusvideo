from __future__ import annotations

from ..schemas import Character, Performance, ShotList
from .base import Role, dump


class Actor(Role):
    name = "Actor"
    persona = """You are a comic actor. You play exactly one character and you stay in their
voice. For each of your lines you choose the delivery, facial expression and body language
that sells the joke. You may tighten wording slightly to fit the voice, but never change a
joke's meaning or another character's lines."""

    def perform(self, character: Character, shots: ShotList) -> Performance:
        mine = [s for s in shots.all_shots()
                if character.name in s.characters or any(l.character == character.name for l in s.dialogue)]
        return self.ask(
            f"Your character:\n{dump(character)}\n\nShots you appear in:\n{dump(mine)}\n\n"
            f"Give your performance as {character.name}. Include a line reading for every line "
            "you speak; for shots where you have no lines, give a silent reaction (text empty).",
            Performance,
        )
