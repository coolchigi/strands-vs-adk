"""The feedback loop, through each framework's real graph engine.

The stages are stubs that log their calls. The reviews return scripted routes. What's under
test is the wiring: a review sending the run forward, back to the same stage, or upstream.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import pytest

from impl.adk import pipeline as adk
from impl.strands import pipeline as strands
from learning.flow import CURRICULUM, DONE, RESEARCH, TEACHING


@dataclass
class Board:
    route: str = RESEARCH


@dataclass
class Script:
    """Stands in for Flow. Each review pops its next route."""

    routes: dict[str, list[str]]
    calls: list[str] = field(default_factory=list)
    board: Board = field(default_factory=Board)

    def _stage(self, name):
        return lambda: self.calls.append(name)

    def _review(self, name):
        def review():
            self.calls.append(name)
            return self.routes[name].pop(0)
        return review

    def __post_init__(self):
        for s in ("research", "curriculum", "teaching"):
            setattr(self, s, self._stage(s))
            setattr(self, f"review_{s}", self._review(f"review_{s}"))


RUNNERS = {"strands": strands.run, "adk": adk.run}


def go(side, **routes):
    base = {"review_research": [CURRICULUM], "review_curriculum": [TEACHING], "review_teaching": [DONE]}
    flow = Script({**base, **{k: list(v) for k, v in routes.items()}})
    RUNNERS[side](flow)
    return flow.calls


@pytest.mark.parametrize("side", RUNNERS)
def test_a_clean_run_goes_straight_through(side):
    assert go(side) == ["research", "review_research", "curriculum", "review_curriculum",
                        "teaching", "review_teaching"]


@pytest.mark.parametrize("side", RUNNERS)
def test_a_review_can_send_its_stage_round_again(side):
    calls = go(side, review_curriculum=[CURRICULUM, TEACHING])
    assert calls[2:6] == ["curriculum", "review_curriculum", "curriculum", "review_curriculum"]


@pytest.mark.parametrize("side", RUNNERS)
def test_a_curriculum_problem_that_started_in_research_goes_back_there(side):
    calls = go(side, review_research=[CURRICULUM, CURRICULUM], review_curriculum=[RESEARCH, TEACHING])
    assert calls[:8] == ["research", "review_research", "curriculum", "review_curriculum",
                         "research", "review_research", "curriculum", "review_curriculum"]
