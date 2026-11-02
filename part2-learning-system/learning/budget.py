"""What a course may cost, and what happens as it gets close.

Each framework's meter collects usage its own way. This is what they share: dollars counted
at the price of the model that answered, a switch to a cheaper model partway through the
lessons so the money left goes further, and a hard stop at the cap itself.

    LEARNING_BUDGET_USD   the most one course may spend. $5 on Gemini, $10 on Claude
    LEARN_SWITCH_AT       how much of what's left for lessons they use before the cheaper model
                          takes over. 0.5 by default, 0 for the cheaper model from the start
    LEARN_CHEAP_MODEL     the cheaper model, if you want a different one. "none" never switches
"""

from __future__ import annotations

import math
import os
from pathlib import Path
from dataclasses import dataclass, field
from datetime import date
from typing import Callable, NamedTuple

# USD per million tokens, (input, output). Output includes Gemini's thinking. Bedrock prices
# from the AWS Price List API (AmazonBedrockFoundationModels, us-east-1, on-demand), Gemini
# from ai.google.dev/gemini-api/docs/pricing, both read 28 September 2026. A US-only inference
# profile ("us.") costs 10% more than a global one ("global.").
PRICES: dict[str, tuple[float, float]] = {
    "global.anthropic.claude-sonnet-4-6": (3.00, 15.00),
    "us.anthropic.claude-sonnet-4-6": (3.30, 16.50),
    "global.anthropic.claude-haiku-4-5": (1.00, 5.00),
    "us.anthropic.claude-haiku-4-5": (1.10, 5.50),
    "gemini-3.8-flash": (0.75, 3.75),  # through 31 December 2026, then PRICE_CHANGES
    "gemini-3.5-flash-lite": (0.30, 2.50),
}
# what writing lessons is charged to (stages.teach_lesson). The switch counts from the first of
# these: counted from $0, 28 Sep's Strands research alone passed it ($7.06 of $10 at today's
# prices), and every lesson would have come from the cheaper model
LESSON_ROLES = ("lesson", "review_lesson")
PLAN_ROLES = ("curriculum", "review_curriculum")  # stages.curriculum and its review
UNKNOWN_MODEL_PRICE = (5.00, 25.00)  # priced high, so an unknown model hits the cap early
# prices a provider has announced will change, from the day they change. Without this the meter
# would count half of what Gemini charges from 2027, and a $5 cap would let about $10 through
PRICE_CHANGES: dict[str, list[tuple[date, tuple[float, float]]]] = {
    "gemini-3.8-flash": [(date(2027, 1, 1), (1.50, 7.50))],
}

# the model each side switches to partway through the lessons
CHEAPER = {
    "global.anthropic.claude-sonnet-4-6": "global.anthropic.claude-haiku-4-5-20251001-v1:0",
    "us.anthropic.claude-sonnet-4-6": "us.anthropic.claude-haiku-4-5-20251001-v1:0",
    "gemini-3.8-flash": "gemini-3.5-flash-lite",
}


def price_for(model: str, on: date | None = None) -> tuple[float, float]:
    """The longest matching name wins, so a profile prefix picks its own price. `on` is today
    unless given, so a build that runs past a price change is charged the new price from then."""
    best = max((name for name in PRICES if name in model), key=len, default=None)
    if best is None:
        return UNKNOWN_MODEL_PRICE
    price = PRICES[best]
    for start, changed in PRICE_CHANGES.get(best, []):
        if (on or date.today()) >= start:
            price = changed
    return price


def dollars(text: str) -> float:
    """A budget the way people write one: 5, 5.00 or $5. Anything else raises ValueError."""
    value = float(text.strip().lstrip("$"))
    if not (value > 0 and math.isfinite(value)):  # "inf" would be no cap at all
        raise ValueError(f"{text!r} isn't an amount more than $0")
    return value


def fraction(text: str) -> float:
    """A share from 0 to 1, like LEARN_SWITCH_AT. 0 means the cheaper model from the start."""
    value = float(text)
    if not 0 <= value <= 1:
        raise ValueError(f"{text!r} isn't between 0 and 1")
    return value


class BudgetExceeded(RuntimeError):
    pass


class StopRequested(BudgetExceeded):
    """Ctrl-C or `learn stop`. Raised where the cap is, so both frameworks stop on it the same way."""


class Projection(NamedTuple):
    """Where the lessons left are headed, if each uses as many tokens as the average so far."""
    end_usd: float           # spent once every lesson is written, allowing for the switch
    cheap_from: int | None   # the lesson the cheaper model starts on
    stop_at: int | None      # the lesson the cap stops the build in
    lesson_usd: float        # one average lesson on the main model
    finish_usd: float        # a cap that should finish the course: every lesson left on the main model,
                             # plus the one the cap interrupts, which is charged and then written again


@dataclass
class Usage:
    calls: int = 0
    input_tokens: int = 0
    output_tokens: int = 0
    usd: float = 0.0


@dataclass
class Budget:
    """Spend by role, the model to use next, and the cap. Meters subclass it."""

    model: str = ""
    limit_usd: float | None = None
    cheap_model: str | None = None
    switch_at: float = 0.5
    by_role: dict[str, Usage] = field(default_factory=dict)
    persist: Callable[[], None] | None = None  # called whenever the count changes
    say: Callable[[str], None] | None = None    # told once, when the model switches
    stop_requested: bool = False                 # Ctrl-C: the next model call is refused
    stop_file: Path | None = None                # or `learn stop`, from anywhere, which leaves this file
    _told: bool = field(default=False, repr=False)

    DEFAULT_LIMIT = "5"  # each meter sets its own

    @classmethod
    def from_env(cls, model: str) -> "Budget":
        # an empty setting once meant no cap at all. Empty now means the default
        limit = os.environ.get("LEARNING_BUDGET_USD", "").strip() or cls.DEFAULT_LIMIT
        cheap = os.environ.get("LEARN_CHEAP_MODEL") or next((c for m, c in CHEAPER.items() if m in model), None)
        return cls(model=model, limit_usd=dollars(limit),
                   cheap_model=None if cheap == "none" else cheap,
                   switch_at=fraction(os.environ.get("LEARN_SWITCH_AT", "").strip() or "0.5"))

    @property
    def total(self) -> Usage:
        u = list(self.by_role.values())
        return Usage(sum(x.calls for x in u), sum(x.input_tokens for x in u),
                     sum(x.output_tokens for x in u), sum(x.usd for x in u))

    @property
    def spent_usd(self) -> float:
        return self.total.usd

    @property
    def price(self) -> tuple[float, float]:
        return price_for(self.current_model())

    @property
    def switch_usd(self) -> float | None:
        """What the course will have spent in all when the cheaper model takes over: what came
        before the lessons, plus switch_at of what that left of the cap. None while that's
        still moving, before the first lesson is charged, and when nothing switches. Worked out
        from the spend by role, so a resumed build gets the same point."""
        if not (self.cheap_model and self.limit_usd):
            return None
        if self.switch_at == 0:
            return 0.0
        lessons = sum(u.usd for r, u in list(self.by_role.items()) if r in LESSON_ROLES)
        if not lessons:
            return None
        before = self.spent_usd - lessons
        return before + self.switch_at * (self.limit_usd - before)

    def spent_on(self) -> tuple[float, float, float]:
        """Research (everything before the plan, the intake included), the course plan, and lessons."""
        rows = list(self.by_role.items())
        plan = sum(u.usd for r, u in rows if r in PLAN_ROLES)
        lessons = sum(u.usd for r, u in rows if r in LESSON_ROLES)
        return sum(u.usd for _, u in rows) - plan - lessons, plan, lessons

    def projection(self, done: int, total: int) -> Projection:
        """The lessons left, played forward at the model each would get and stopped at the cap."""
        rows = [u for r, u in list(self.by_role.items()) if r in LESSON_ROLES]
        tokens_in = sum(u.input_tokens for u in rows) / max(done, 1)
        tokens_out = sum(u.output_tokens for u in rows) / max(done, 1)

        def cost(model: str) -> float:
            p = price_for(model)
            return (tokens_in * p[0] + tokens_out * p[1]) / 1_000_000

        spent, point, lesson = self.spent_usd, self.switch_usd, cost(self.model)
        finish = spent + (total - done + 1) * lesson
        cheap_from = None
        for k in range(done + 1, total + 1):
            on_cheap = point is not None and spent >= point
            if on_cheap and cheap_from is None:
                cheap_from = k
            spent += cost(self.cheap_model if on_cheap else self.model)
            if self.limit_usd is not None and spent >= self.limit_usd:
                return Projection(spent, cheap_from, k, lesson, finish)
        return Projection(spent, cheap_from, None, lesson, finish)

    def current_model(self) -> str:
        """The main model until the switch point, then the cheaper one. Research and the course
        plan stay on the main model, however much they cost, and the cap still stops them.
        A switch_at of 0 puts everything on the cheaper model."""
        point = self.switch_usd
        if point is not None and self.spent_usd >= point:
            if not self._told and self.say is not None:
                self.say(f"${self.spent_usd:.2f} spent of your ${self.limit_usd:.2f} cap, so the rest of this "
                         f"course is written by a cheaper model ({self.cheap_model}).")
            self._told = True
            return self.cheap_model
        return self.model

    def charge(self, role: str, tokens_in: int, tokens_out: int, model: str | None = None) -> None:
        """Count tokens at the price of the model that used them."""
        p = price_for(model or self.current_model())
        u = self.by_role.setdefault(role, Usage())
        u.input_tokens += tokens_in
        u.output_tokens += tokens_out
        u.usd += (tokens_in * p[0] + tokens_out * p[1]) / 1_000_000
        if self.persist is not None:
            self.persist()

    def check(self) -> None:
        """Before a call: refuse it once the course is at its cap, or once Ctrl-C or `learn stop` asked to stop."""
        if self.stop_file is not None and self.stop_file.exists():
            self.stop_requested = True
        if self.stop_requested:
            raise StopRequested("stopped")
        if self.limit_usd is not None and self.spent_usd >= self.limit_usd:
            raise BudgetExceeded(f"spent ${self.spent_usd:.2f} of a ${self.limit_usd:.2f} cap. "
                                 "Raise LEARNING_BUDGET_USD to go further.")
