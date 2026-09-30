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

from . import checks, prompts, stages
from .model import Course, CourseFile, Curriculum, KnowledgeBase, LearnerProfile, Lesson, Problem, Stage
from .stages import Brain, Checkpoint, Review, Say, quiet
from .web import Web

log = logging.getLogger("learning")

RESEARCH, CURRICULUM, TEACHING, DONE = "research", "curriculum", "teaching", "done"

STAGE_NAMES = {RESEARCH: "research", CURRICULUM: "course plan"}


def notes(problems: list) -> str:
    return f"{len(problems)} note{'s' if len(problems) != 1 else ''}"


@dataclass
class Board:
    profile: LearnerProfile
    knowledge: KnowledgeBase | None = None
    version_problem: str | None = None
    curriculum: Curriculum | None = None
    lessons: dict[str, Lesson] = field(default_factory=dict)
    problems: dict[str, list[Problem]] = field(default_factory=dict)  # what's still wrong, by stage
    reasons: list[str] = field(default_factory=list)                  # why the next stage runs again
    facts: list[str] = field(default_factory=list)                    # checked against the world, kept
    attempts: dict[str, int] = field(default_factory=dict)
    decided: set[str] = field(default_factory=set)                    # loaded from a checkpoint
    route: str = RESEARCH


@dataclass
class Flow:
    brain: Brain
    web: Web
    board: Board
    checkpoint: Checkpoint
    max_attempts: int = 3
    reviewer: bool = True
    say: Say = quiet  # plain-language progress for whoever's watching. The details go to the log

    def _tick(self, stage: str) -> int:
        self.board.attempts[stage] = self.board.attempts.get(stage, 0) + 1
        return self.board.attempts[stage]

    def _decide(self, stage: str, problems: list[Problem], forward: str, back: dict[Stage, str]) -> str:
        """Where the run goes after a review."""
        b = self.board
        b.problems[stage] = problems
        self.checkpoint.save_problems(b.problems)
        self.checkpoint.log({"stage": stage, "attempt": b.attempts.get(stage, 0),
                             "problems": [p.model_dump(mode="json") for p in problems]})
        if not problems:
            b.reasons = []
            return forward
        for p in problems:
            log.info("  %s %s: %s", stage, p.check, p.detail[:240])
        name = STAGE_NAMES.get(stage, stage)
        if b.attempts.get(stage, 0) >= self.max_attempts:
            log.info("%s: out of attempts, going forward with %d problems recorded", stage, len(problems))
            self.say(f"Moving on. The reviewer still had {notes(problems)} on the {name}, "
                     "and the course lists them")
            b.reasons = []
            return forward
        b.reasons = [p.detail for p in problems]
        # a problem that started upstream goes back there
        upstream = [back[p.stage] for p in problems if p.stage in back]
        route = upstream[0] if upstream else stage
        self.say(f"The reviewer had {notes(problems)} on the {name}, "
                 f"so the {STAGE_NAMES.get(route, route)} gets another pass")
        return route

    # -- research ----------------------------------------------------------------------

    def research(self) -> None:
        b = self.board
        saved = self.checkpoint.load("knowledge", KnowledgeBase)
        if saved and not b.reasons:
            b.knowledge = saved
            b.decided.add(RESEARCH)
            self.say(f"✓ Research already done: {len(saved.claims)} facts checked")
            return
        b.decided.discard(RESEARCH)
        self._tick(RESEARCH)
        known = b.knowledge or saved
        if b.reasons and known is not None:
            self.say("Looking for pages that fill the gaps")
            result = stages.revise_research(self.brain, self.web, known, b.reasons, self.say)
        else:
            result = stages.research(self.brain, self.web, b.profile, b.reasons or None, self.say)
        b.knowledge, b.version_problem = result.knowledge, result.version_problem

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
        route = self._decide(RESEARCH, problems, CURRICULUM, {})
        if route == CURRICULUM:
            self.checkpoint.save("knowledge", b.knowledge)
        return route

    # -- curriculum ---------------------------------------------------------------------

    def curriculum(self) -> None:
        b = self.board
        saved = self.checkpoint.load("curriculum", Curriculum)
        if saved and not b.reasons:
            b.curriculum = saved
            b.decided.add(CURRICULUM)
            self.say(f"✓ Course plan already done: {len(saved.units)} units, {len(saved.lessons())} lessons")
            return
        b.decided.discard(CURRICULUM)
        self._tick(CURRICULUM)
        self.say("Planning the units and lessons")
        b.curriculum = stages.curriculum(self.brain, b.knowledge, b.reasons or None)
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
            saved = self.checkpoint.load(f"lessons/{spec.id}", Lesson)
            if saved is not None:
                b.lessons[spec.id] = saved
                self.say(f"✓ Lesson {i} of {len(specs)} already written: {spec.title}")
            else:
                self.say(f"Writing lesson {i} of {len(specs)}: {spec.title}")
                result = stages.teach_lesson(self.brain, b.knowledge, spec, previous, b.facts, self.reviewer,
                                             self.say)
                b.lessons[spec.id] = result.lesson
                b.problems[f"lesson {spec.id}"] = result.problems
                self.checkpoint.save_problems(b.problems)
                self.checkpoint.save(f"lessons/{spec.id}", result.lesson)
                self.say("    ✓ passed its checks" if not result.problems else
                         f"    still has {len(result.problems)} problem{'s' if len(result.problems) > 1 else ''} "
                         f"after {result.attempts} tries. "
                         "They're listed at the top of the lesson")
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
    board = Board(profile=profile, problems=checkpoint.load_problems())
    return Flow(brain=brain, web=web, board=board, checkpoint=checkpoint, **kw)
