"""The run, as stages and reviews. Each framework turns these into graph nodes and edges.

```text
research ─▶ review research ─▶ curriculum ─▶ review curriculum ─▶ teaching ─▶ review teaching ─▶ done
   ▲              │                ▲                 │  │              ▲             │
   └──── again ───┘                └──── again ──────┘  └─ research     └── lessons ──┘
```

A review decides where the run goes: forward, the same stage again with reasons, or back
to an earlier stage when that's where the problem started. Stages don't repeat forever:
after `max_attempts` a stage goes forward with its problems recorded, and the course says so.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable

from pydantic import BaseModel, Field

from . import checks, prompts, stages
from .course_dir import slug
from .model import Course, CourseFile, Curriculum, KnowledgeBase, LearnerProfile, Lesson, Problem, Stage
from .stages import Brain, Checkpoint, Review, Say, quiet
from .web import Web

log = logging.getLogger("learning")

RESEARCH, CURRICULUM, TEACHING, DONE = "research", "curriculum", "teaching", "done"

STAGE_NAMES = {RESEARCH: "research", CURRICULUM: "course plan"}


def notes(problems: list) -> str:
    return f"{len(problems)} note{'s' if len(problems) != 1 else ''}"


def sized(plan: Curriculum) -> str:
    units, lessons = len(plan.units), len(plan.lessons())
    return f"{units} unit{'s' if units != 1 else ''}, {lessons} lesson{'s' if lessons != 1 else ''}"


@dataclass
class Board:
    profile: LearnerProfile
    knowledge: KnowledgeBase | None = None
    version_problem: str | None = None
    curriculum: Curriculum | None = None
    lessons: dict[str, Lesson] = field(default_factory=dict)
    problems: dict[str, list[Problem]] = field(default_factory=dict)  # what's still wrong, by stage
    reasons: list[str] = field(default_factory=list)                  # why the next stage runs again
    reasons_for: str | None = None                                    # and which stage that is
    reviewed: dict[str, int] = field(default_factory=dict)            # the last attempt each review decided on
    passed: dict[str, int] = field(default_factory=dict)              # and the last one it sent forward
    facts: list[str] = field(default_factory=list)                    # checked against the world, kept
    attempts: dict[str, int] = field(default_factory=dict)
    decided: set[str] = field(default_factory=set)                    # loaded from a checkpoint
    route: str = RESEARCH


class BoardState(BaseModel):
    """What a run has decided, kept as it changes. Without it a resumed run started its retries
    from 0, forgot a review's request to redo research, and dropped the facts it had checked."""
    attempts: dict[str, int] = Field(default_factory=dict)
    reviewed: dict[str, int] = Field(default_factory=dict)
    passed: dict[str, int] = Field(default_factory=dict)
    reasons: list[str] = Field(default_factory=list)
    reasons_for: str | None = None
    facts: list[str] = Field(default_factory=list)


@dataclass
class Flow:
    brain: Brain
    web: Web
    board: Board
    checkpoint: Checkpoint
    max_attempts: int = 3
    reviewer: bool = True
    say: Say = quiet  # plain-language progress for whoever's watching. The details go to the log
    on_lesson: Callable[[int, int], None] | None = None  # told (written, of) after each lesson this run writes

    def _tick(self, stage: str) -> int:
        self.board.attempts[stage] = self.board.attempts.get(stage, 0) + 1
        self._keep_board()
        return self.board.attempts[stage]

    def _keep_board(self) -> None:
        b = self.board
        self.checkpoint.save("board", BoardState(attempts=b.attempts, reviewed=b.reviewed, passed=b.passed,
                                                 reasons=b.reasons, reasons_for=b.reasons_for, facts=b.facts))

    def _again(self, stage: str) -> list[str]:
        """The reasons a review gave for running this stage again, if it was this stage it sent back."""
        return self.board.reasons if self.board.reasons_for == stage else []

    def _decide(self, stage: str, problems: list[Problem], forward: str, back: dict[Stage, str]) -> str:
        """Where the run goes after a review."""
        b = self.board
        b.problems[stage] = problems
        b.reviewed[stage] = b.attempts.get(stage, 0)
        self.checkpoint.save_problems(b.problems)
        self.checkpoint.log({"stage": stage, "attempt": b.attempts.get(stage, 0),
                             "problems": [p.model_dump(mode="json") for p in problems]})
        if not problems:
            b.reasons, b.reasons_for = [], None
            b.passed[stage] = b.attempts.get(stage, 0)
            self._keep_board()
            return forward
        for p in problems:
            log.info("  %s %s: %s", stage, p.check, p.detail[:240])
        name = STAGE_NAMES.get(stage, stage)
        if b.attempts.get(stage, 0) >= self.max_attempts:
            log.info("%s: out of attempts, going forward with %d problems recorded", stage, len(problems))
            self.say(f"Moving on. The reviewer still had {notes(problems)} on the {name}, "
                     "and the course lists them")
            b.reasons, b.reasons_for = [], None
            b.passed[stage] = b.attempts.get(stage, 0)
            self._keep_board()
            return forward
        b.reasons = [p.detail for p in problems]
        # a problem that started upstream goes back there
        upstream = [back[p.stage] for p in problems if p.stage in back]
        route = upstream[0] if upstream else stage
        b.reasons_for = route
        self._keep_board()
        self.say(f"The reviewer had {notes(problems)} on the {name}, "
                 f"so the {STAGE_NAMES.get(route, route)} gets another pass")
        return route

    # -- research ----------------------------------------------------------------------

    def research(self) -> None:
        b = self.board
        saved = self.checkpoint.load("knowledge", KnowledgeBase)
        again = self._again(RESEARCH)
        draft = self.checkpoint.load("research_draft", stages.ResearchDraft)
        n, reviewed = b.attempts.get(RESEARCH, 0), b.reviewed.get(RESEARCH, 0)
        if draft and draft.attempt == n == b.passed.get(RESEARCH) and not again:
            # its review sent it forward. A stop before knowledge.json was written left it missing,
            # or holding the pass before a revision the plan asked for
            if saved != draft.knowledge:
                self.checkpoint.save("knowledge", draft.knowledge)
            saved = draft.knowledge
        if saved and not again:
            b.knowledge = saved
            b.decided.add(RESEARCH)
            self.say(f"✓ Research already done: {len(saved.claims)} facts checked")
            return
        b.decided.discard(RESEARCH)
        if draft and draft.attempt == n and reviewed < n:
            # this pass finished before the run stopped, and its review is still to come
            b.knowledge, b.version_problem = draft.knowledge, draft.version_problem
            self.say(f"✓ Research already done: {len(draft.knowledge.claims)} facts checked")
            return
        if n <= reviewed:  # a pass that stopped partway carries on as the same attempt
            n = self._tick(RESEARCH)
        known = b.knowledge or (draft.knowledge if draft else None) or saved
        if again and known is not None:
            self.say("Looking for pages that fill the gaps")
            result = stages.revise_research(self.brain, self.web, known, again, self.say)
        else:
            progress = self.checkpoint.load("research_progress", stages.ResearchProgress)
            result = stages.research(self.brain, self.web, b.profile, again or None, self.say,
                                     progress=progress if progress and progress.attempt == n else None,
                                     keep=lambda p: self.checkpoint.save("research_progress",
                                                                        p.model_copy(update={"attempt": n})))
        b.knowledge, b.version_problem = result.knowledge, result.version_problem
        self.checkpoint.save("research_draft", stages.ResearchDraft(attempt=n, knowledge=result.knowledge,
                                                                    version_problem=result.version_problem))

    def review_research(self) -> str:
        b = self.board
        if RESEARCH in b.decided:
            return CURRICULUM  # its review sent it forward before the run stopped
        problems = checks.research(b.knowledge, b.version_problem)
        # the reviewer runs even when a check failed. Waiting for the checks to pass once let
        # one objective with no evidence use up every attempt, and the reviewer, the only one
        # who asks what's missing, never saw the research
        if self.reviewer:
            found = "\n".join(f"- {p.detail}" for p in problems) or "(nothing)"
            review = self.brain.ask("review_research", prompts.REVIEW_RESEARCH,
                                    f"Learner:\n{b.profile.brief()}\n\nObjectives:\n{stages.tree_listing(b.knowledge)}"
                                    f"\n\nClaims:\n{stages.claim_listing(b.knowledge)}"
                                    f"\n\nWhat the mechanical checks found:\n{found}", Review)
            problems += [Problem(stage=Stage.RESEARCH, check="review", detail=f.detail) for f in review.findings]
        # a revision can't fix the version: finding the spec already asked twice. The problem is
        # kept and the course leaves the version out, without spending research attempts on it
        noted = [p for p in problems if p.check == "version_unverified"]
        route = self._decide(RESEARCH, [p for p in problems if p not in noted], CURRICULUM, {})
        if noted:
            b.problems[RESEARCH] = b.problems[RESEARCH] + noted
            self.checkpoint.save_problems(b.problems)
            self.checkpoint.log({"stage": RESEARCH, "noted": [p.model_dump(mode="json") for p in noted]})
        if route == CURRICULUM:
            self.checkpoint.save("knowledge", b.knowledge)
        return route

    # -- curriculum ---------------------------------------------------------------------

    def curriculum(self) -> None:
        b = self.board
        saved = self.checkpoint.load("curriculum", Curriculum)
        again = self._again(CURRICULUM)
        if saved and not again:
            b.curriculum = saved
            b.decided.add(CURRICULUM)
            self.say(f"✓ Course plan already done: {sized(saved)}")
            return
        b.decided.discard(CURRICULUM)
        draft = self.checkpoint.load("curriculum_draft", stages.CurriculumDraft)
        n, reviewed = b.attempts.get(CURRICULUM, 0), b.reviewed.get(CURRICULUM, 0)
        # a plan written before the run stopped: its review is still to come, or it passed and the
        # run stopped before curriculum.json was written. A plan sent back, to research or itself, isn't
        if draft and draft.attempt == n and (reviewed < n or b.passed.get(CURRICULUM) == n):
            b.curriculum = draft.curriculum
            if reviewed >= n:
                self.checkpoint.save("curriculum", draft.curriculum)
                b.decided.add(CURRICULUM)
            self.say(f"✓ Course plan already done: {sized(draft.curriculum)}")
            return
        if n <= reviewed:  # a plan that stopped partway is the same attempt
            n = self._tick(CURRICULUM)
        self.say("Planning the units and lessons")
        b.curriculum = stages.curriculum(self.brain, b.knowledge, again or None)
        self.checkpoint.save("curriculum_draft", stages.CurriculumDraft(attempt=n, curriculum=b.curriculum))
        self.say(f"✓ Planned {len(b.curriculum.units)} units, {len(b.curriculum.lessons())} lessons")

    def review_curriculum(self) -> str:
        b = self.board
        if CURRICULUM in b.decided:
            return TEACHING
        problems = checks.curriculum(b.curriculum, b.knowledge)
        if not problems and self.reviewer:
            review = self.brain.ask("review_curriculum", prompts.REVIEW_CURRICULUM,
                                    f"Learner:\n{b.profile.brief()}\n\nObjectives:\n{stages.tree_listing(b.knowledge)}"
                                    f"\n\nCurriculum:\n{b.curriculum.model_dump_json(indent=1)}", Review)
            problems = [Problem(stage=f.stage if f.stage is Stage.RESEARCH else Stage.CURRICULUM,
                                check="review", detail=f.detail, lesson_id=f.lesson_id) for f in review.findings]
        route = self._decide(CURRICULUM, problems, TEACHING, {Stage.RESEARCH: RESEARCH})
        if route == TEACHING:
            self.checkpoint.save("curriculum", b.curriculum)
        return route

    # -- teaching -------------------------------------------------------------------------

    def teaching(self) -> None:
        """Every lesson, in order, each starting from the previous lesson's finished files.

        Each lesson has its own loop of writing, checking and rewriting, so one bad lesson
        costs its own retries, not the whole course's.
        """
        b = self.board
        self._tick(TEACHING)
        previous: list[CourseFile] = []
        specs = b.curriculum.lessons()
        for i, spec in enumerate(specs, 1):
            # named the way its folder is: a raw id like ../knowledge once overwrote the research
            key = f"lessons/{slug(spec.id) or 'lesson'}"
            saved = self.checkpoint.load(key, Lesson)
            if saved is not None:
                b.lessons[spec.id] = saved
                self.say(f"✓ Lesson {i} of {len(specs)} already written: {spec.title}")
            else:
                self.say(f"Writing lesson {i} of {len(specs)}: {spec.title}")
                drafted = f"lesson_drafts/{slug(spec.id) or 'lesson'}"
                result = stages.teach_lesson(self.brain, b.knowledge, spec, previous, b.facts, self.reviewer,
                                             self.say, draft=self.checkpoint.load(drafted, stages.LessonDraft),
                                             keep=lambda d, at=drafted: self.checkpoint.save(at, d))
                b.lessons[spec.id] = result.lesson
                b.problems[f"lesson {spec.id}"] = result.problems
                self.checkpoint.save_problems(b.problems)
                self.checkpoint.save(key, result.lesson)
                self._keep_board()  # the facts this lesson checked hold for the next ones too
                self.say("    ✓ passed its checks" if not result.problems else
                         f"    still has {len(result.problems)} problem{'s' if len(result.problems) > 1 else ''} "
                         f"after {result.attempts} tries. "
                         "They're listed at the top of the lesson")
                if self.on_lesson is not None:
                    self.on_lesson(i, len(specs))
            if b.lessons[spec.id].exercise:
                previous = b.lessons[spec.id].exercise.solution

    def review_teaching(self) -> str:
        b = self.board
        left = {k: v for k, v in b.problems.items() if k.startswith("lesson ") and v}
        if left:
            log.info("%d lessons still have problems after their retries: %s", len(left), sorted(left))
        return DONE

    # -- the result -------------------------------------------------------------------------

    def course(self) -> Course:
        b = self.board
        order = [s.id for s in b.curriculum.lessons()]
        return stages.assemble(b.knowledge, b.curriculum, [b.lessons[i] for i in order if i in b.lessons],
                               open_problems(b))


def open_problems(board: Board) -> list[Problem]:
    return [p for ps in board.problems.values() for p in ps]


def start(brain: Brain, web: Web, profile: LearnerProfile, run_dir: Path, **kw) -> Flow:
    checkpoint = Checkpoint(run_dir)
    kept = checkpoint.load("board", BoardState) or BoardState()
    board = Board(profile=profile, problems=checkpoint.load_problems(), attempts=dict(kept.attempts),
                  reviewed=dict(kept.reviewed), passed=dict(kept.passed), reasons=list(kept.reasons),
                  reasons_for=kept.reasons_for, facts=list(kept.facts))
    return Flow(brain=brain, web=web, board=board, checkpoint=checkpoint, **kw)
