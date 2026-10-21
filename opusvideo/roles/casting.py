from __future__ import annotations

from ..schemas import Brief, Cast, Script
from .base import Role, dump


class RoleCreator(Role):
    name = "Role Creator"
    persona = """You are the casting director and character designer. For every speaking
character in the script you define who they are and how they are funny, and you write a locked
visual bible: a precise physical description (face shape, hair, skin tone, build, age, wardrobe
with colours, signature prop) detailed enough that an image model renders the same person in
every shot. Make characters visually distinct from each other at a glance. Never base a
character on a real person."""

    def cast(self, brief: Brief, script: Script) -> Cast:
        return self.ask(f"Brief:\n{dump(brief)}\n\nScript:\n{dump(script)}\n\n"
                        "Create the cast. Use the exact character names from the script.", Cast)
