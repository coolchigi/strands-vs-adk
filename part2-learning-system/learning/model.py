"""What every stage hands to the next. Shared by both frameworks.

The order follows backward design: what the learner must be able to do (objectives),
what proves they can (assessments), and only then the lessons.
"""

from __future__ import annotations

import hashlib
import re
from datetime import datetime, timezone
from enum import Enum

from pydantic import BaseModel, Field, field_validator


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def short_id(*parts: str) -> str:
    return hashlib.sha256("\x1f".join(parts).encode()).hexdigest()[:12]


_LINK = re.compile(r"!?\[([^\]]*)\]\([^)]*\)")
_MARKS = re.compile(r"\*\*|__|`")
_ESCAPE = re.compile(r"\\([\\`*_{}\[\]()#+\-.!])")


def normalise(text: str) -> str:
    """Quote matching survives whitespace, smart quotes and inline markup, nothing more."""
    text = _ESCAPE.sub(r"\1", text)
    text = _LINK.sub(r"\1", text)
    text = _MARKS.sub("", text)
    text = text.replace("’", "'").replace("‘", "'")
    text = text.replace("“", '"').replace("”", '"')
    return re.sub(r"\s+", " ", text).strip().lower()


# -- who is learning, and why -------------------------------------------------

class SubjectKind(str, Enum):
    CERTIFICATION = "certification"
    TOOL = "tool"
    LANGUAGE = "language"
    CONCEPT = "concept"


class LearnerProfile(BaseModel):
    """What the intake works out. Every later stage reads it."""

    subject: str = Field(default="", description="The thing to learn, named the way its docs name it")
    kind: SubjectKind = SubjectKind.TOOL
    goal: str = Field(default="", description="What they want out of it, in their words")
    starting_point: str = Field(default="", description="What they already know. Empty if unsaid.")
    target: str = Field(default="", description="What they want to be able to build or do. Empty if unsaid.")
    constraints: list[str] = Field(default_factory=list,
                                   description="Things that limit the course: no cloud account, time, OS")
    subject_is_clear: bool = Field(default=False, description="True when specific enough to research")
    questions: list[str] = Field(default_factory=list,
                                 description="Up to 3 questions whose answers would change the course")

    def brief(self) -> str:
        lines = [f"Subject: {self.subject} ({self.kind.value})"]
        for label, value in (("Goal", self.goal), ("Starting from", self.starting_point),
                             ("Wants to be able to", self.target)):
            if value:
                lines.append(f"{label}: {value}")
        if self.constraints:
            lines.append("Constraints: " + "; ".join(self.constraints))
        return "\n".join(lines)


# -- the spec of what must be learned -------------------------------------------

class Tier(str, Enum):
    OFFICIAL = "official"
    VENDOR = "vendor"
    COMMUNITY = "community"


class Source(BaseModel):
    id: str
    url: str
    title: str = ""
    tier: Tier = Tier.OFFICIAL
    content: str = Field(default="", repr=False)
    content_hash: str = ""
    fetched_at: datetime = Field(default_factory=utcnow)

    @classmethod
    def build(cls, url: str, title: str, content: str, tier: Tier) -> "Source":
        return cls(id=short_id(url), url=url, title=title, tier=tier, content=content,
                   content_hash=hashlib.sha256(content.encode()).hexdigest())


class Objective(BaseModel):
    """One thing the learner must be able to do, and where that requirement comes from."""

    id: str = Field(description="Dotted, like 2 or 2.3")
    statement: str = Field(description="What the learner must be able to do")
    parent_id: str | None = None
    weight: float | None = Field(default=None, description="Share of the exam, if the spec gives one")
    source_url: str = ""
    quote: str = Field(default="", description="The words in the spec or docs this comes from")


class Practice(BaseModel):
    """Something practitioners do routinely, and the objective that teaches it."""

    task: str
    objective_id: str = Field(default="", description="The objective that teaches all of it. Empty if none does")


class Spec(BaseModel):
    """What defines the scope. An exam guide, or the official docs when there is none."""

    kind: str = Field(description="exam_guide or derived_from_docs")
    title: str
    urls: list[str] = Field(default_factory=list)
    version: str | None = None
    version_url: str | None = None
    version_quote: str | None = None
    objectives: list[Objective] = Field(default_factory=list)
    practice: list[Practice] = Field(default_factory=list, description="What practitioners do routinely")

    @field_validator("practice", mode="before")
    @classmethod
    def _plain_practice(cls, items: list) -> list:
        # research saved before coverage was tracked wrote each item as a plain string
        return [{"task": i} if isinstance(i, str) else i for i in items or []]

    def leaves(self) -> list[Objective]:
        parents = {o.parent_id for o in self.objectives if o.parent_id}
        return [o for o in self.objectives if o.id not in parents]


class Claim(BaseModel):
    id: str
    text: str
    quote: str
    source_id: str
    objective_ids: list[str] = Field(default_factory=list)


class Dropped(BaseModel):
    url: str
    quote: str = ""
    reason: str


class KnowledgeBase(BaseModel):
    """Everything the researcher hands the curriculum builder."""

    profile: LearnerProfile
    spec: Spec
    sources: list[Source] = Field(default_factory=list)
    claims: list[Claim] = Field(default_factory=list)
    dropped: list[Dropped] = Field(default_factory=list)
    problems: list[str] = Field(default_factory=list, description="What research could not settle")

    def claims_for(self, objective_id: str) -> list[Claim]:
        return [c for c in self.claims if objective_id in c.objective_ids]

    def coverage(self) -> dict[str, int]:
        return {o.id: len(self.claims_for(o.id)) for o in self.spec.leaves()}


# -- the curriculum -------------------------------------------------------------

class Level(str, Enum):
    """Bloom's revised taxonomy, the cognitive process an objective asks for."""

    REMEMBER = "remember"
    UNDERSTAND = "understand"
    APPLY = "apply"
    ANALYZE = "analyze"
    EVALUATE = "evaluate"
    CREATE = "create"


class Evidence(str, Enum):
    EXERCISE = "exercise"   # the learner builds or changes something, and a check runs it
    QUIZ = "quiz"           # questions, answered before the answer is shown
    PROJECT = "project"     # unguided, at the end of a unit


class LessonObjective(BaseModel):
    statement: str = Field(description="Measurable: a verb and what it acts on")
    level: Level
    covers: list[str] = Field(default_factory=list, description="Objective ids from the spec")
    evidence: Evidence = Field(description="What proves the learner can do it")


class LessonSpec(BaseModel):
    id: str = Field(description="Like u2-l3")
    title: str
    objectives: list[LessonObjective] = Field(default_factory=list)
    prerequisites: list[str] = Field(default_factory=list, description="Lesson ids that must come first")
    claim_ids: list[str] = Field(default_factory=list, description="Claims this lesson teaches from")
    reviews: list[str] = Field(default_factory=list, description="Earlier lesson ids this one revisits")
    exercise_idea: str = Field(default="", description="What the learner builds or changes")


class Unit(BaseModel):
    id: str = Field(description="Like u2")
    title: str
    outcomes: list[str] = Field(default_factory=list, description="What the learner can do after the unit")
    lessons: list[LessonSpec] = Field(default_factory=list)
    project: str = Field(default="", description="An unguided project that ends the unit")


class Curriculum(BaseModel):
    title: str
    summary: str = ""
    outcomes: list[str] = Field(default_factory=list, description="What the learner can do at the end")
    units: list[Unit] = Field(default_factory=list)

    def lessons(self) -> list[LessonSpec]:
        return [l for u in self.units for l in u.lessons]


# -- lessons ------------------------------------------------------------------------

class CourseFile(BaseModel):
    path: str = Field(description="Relative to the exercise folder, like main.tf")
    content: str


class QuizItem(BaseModel):
    stem: str = Field(description="The question. A scenario where the objective asks for one.")
    options: list[str] = Field(description="3 or 4 options, one right")
    answer: int = Field(description="Index of the right option")
    explanation: str = Field(description="Why the answer is right, and why the tempting wrong ones are wrong")
    objective: str = Field(description="The lesson objective this tests, word for word")


class Exercise(BaseModel):
    task: str = Field(description="What to do, specific enough to start without guessing")
    starter: list[CourseFile] = Field(default_factory=list, description="What the learner starts from, with gaps")
    solution: list[CourseFile] = Field(default_factory=list, description="The finished files")
    checks: list[CourseFile] = Field(default_factory=list, description="Tests the learner runs")
    hints: list[str] = Field(default_factory=list, description="From gentle to specific")


class Lesson(BaseModel):
    id: str
    title: str
    recall: str = Field(default="", description="What earlier lessons established, briefly")
    explanation: str = Field(description="Markdown. Every factual sentence cites a claim as [c:ID]")
    worked_example: str = Field(description="Markdown. One example, worked through")
    exercise: Exercise | None = None
    quiz: list[QuizItem] = Field(default_factory=list)


class Course(BaseModel):
    """What the learner gets. Written to disk as a folder."""

    profile: LearnerProfile
    knowledge: KnowledgeBase
    curriculum: Curriculum
    lessons: list[Lesson] = Field(default_factory=list)
    problems: list[Problem] = Field(default_factory=list, description="What the checks and reviews still found")
    built_at: datetime = Field(default_factory=utcnow)


# -- review ---------------------------------------------------------------------------

class Stage(str, Enum):
    RESEARCH = "research"
    CURRICULUM = "curriculum"
    TEACHING = "teaching"


class Problem(BaseModel):
    stage: Stage
    check: str
    detail: str
    lesson_id: str | None = None


Course.model_rebuild()
