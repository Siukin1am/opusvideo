"""Typed contracts passed between crew members.

Every Claude role returns one of these models via structured outputs, so the
next role can consume it directly.
"""

from __future__ import annotations

from typing import List, Literal

from pydantic import BaseModel, Field


class Brief(BaseModel):
    premise: str
    audience: str = "general adult audience"
    tone: str = "playful, absurd, warm"
    duration_sec: int = 60
    style: str = "live-action sitcom look, bright natural lighting"
    language: str = "English"


# ---------- Writer ----------

class Pitch(BaseModel):
    title: str
    logline: str
    comedic_engine: str = Field(description="The core mechanism that generates the jokes")
    beats: List[str] = Field(description="Setup, escalation and payoff in a few beats")


class PitchDeck(BaseModel):
    pitches: List[Pitch]


class Line(BaseModel):
    character: str
    text: str
    parenthetical: str = ""


class ScriptScene(BaseModel):
    scene_id: str = Field(description="Stable id like S1, S2")
    setting: str
    summary: str
    comedic_beat: str
    lines: List[Line]


class Script(BaseModel):
    title: str
    logline: str
    scenes: List[ScriptScene]
    ending_tag: str = Field(description="The final button / last laugh")


# ---------- Advisor ----------

class Note(BaseModel):
    scene_id: str
    issue: str
    suggestion: str
    severity: Literal["minor", "major", "critical"]


class AdvisorNotes(BaseModel):
    overall: str
    strengths: List[str]
    notes: List[Note]
    funniest_moment: str
    weakest_moment: str


# ---------- Examiner ----------

class Score(BaseModel):
    criterion: str
    score: int = Field(description="1 (bad) to 10 (excellent)")
    comment: str


class Evaluation(BaseModel):
    scores: List[Score]
    overall: int = Field(description="1 to 10")
    passed: bool
    blocking_issues: List[str]


class KeyframeReview(BaseModel):
    shot_id: str
    characters_consistent: bool
    matches_prompt: bool
    score: int = Field(description="1 to 10")
    issues: List[str]
    regenerate: bool
    prompt_fix: str = Field(description="How to change the image prompt if regenerating; empty otherwise")


# ---------- Chief Decider ----------

class PitchChoice(BaseModel):
    chosen_index: int = Field(description="0-based index of the winning pitch")
    rationale: str
    directives: List[str]


class Decision(BaseModel):
    verdict: Literal["approve", "revise", "kill"]
    rationale: str
    directives: List[str] = Field(description="Concrete instructions for the next draft")


# ---------- Role Creator ----------

class Character(BaseModel):
    name: str
    role_in_story: str
    personality: str
    comedic_trait: str
    voice: str = Field(description="How they sound: pace, pitch, verbal tics")
    age_range: str
    visual_bible: str = Field(
        description="Exhaustive, reusable physical description: face, hair, build, skin, "
        "wardrobe, colours, props. Pasted verbatim into every image prompt."
    )


class Cast(BaseModel):
    characters: List[Character]


# ---------- Director ----------

class Shot(BaseModel):
    shot_id: str = Field(description="Stable id like S1-01")
    duration_sec: int = Field(description="3 to 10")
    shot_type: str = Field(description="wide, medium, close-up, insert, ...")
    camera_move: str
    action: str
    characters: List[str]
    dialogue: List[Line]
    comedic_timing: str


class DirectedScene(BaseModel):
    scene_id: str
    location_visual: str
    mood: str
    shots: List[Shot]


class ShotList(BaseModel):
    visual_style: str
    scenes: List[DirectedScene]

    def all_shots(self) -> List[Shot]:
        return [shot for scene in self.scenes for shot in scene.shots]


# ---------- Actor ----------

class LineReading(BaseModel):
    shot_id: str
    text: str
    delivery: str
    facial_expression: str
    body_language: str


class Performance(BaseModel):
    character: str
    acting_choices: str
    line_readings: List[LineReading]


# ---------- Prompt Engineer ----------

class ShotPrompt(BaseModel):
    shot_id: str
    image_prompt: str
    video_prompt: str
    negative_prompt: str


class PromptBook(BaseModel):
    style_prefix: str
    prompts: List[ShotPrompt]


# ---------- Final review ----------

class FinalReview(BaseModel):
    verdict: Literal["ship", "reshoot"]
    rationale: str
    reshoot_shot_ids: List[str]
