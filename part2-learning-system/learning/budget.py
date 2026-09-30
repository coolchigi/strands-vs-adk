"""What a course may cost, and what happens as it gets close.

Each framework's meter collects usage its own way. This is what they share: dollars counted
at the price of the model that answered, a switch to a cheaper model partway to the cap so
the course finishes instead of stopping, and a hard stop at the cap itself.

    LEARNING_BUDGET_USD   the most one course may spend. $5 on Gemini, $10 on Claude
    LEARN_SWITCH_AT       how far into it to switch to the cheaper model. 0.5 by default
    LEARN_CHEAP_MODEL     the cheaper model, if you want a different one. "none" never switches
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Callable

# USD per million tokens, (input, output). Output includes Gemini's thinking. Bedrock prices
# from the AWS Price List API (AmazonBedrockFoundationModels, us-east-1, on-demand), Gemini
# from ai.google.dev/gemini-api/docs/pricing, both read 28 September 2026. A US-only inference
# profile ("us.") costs 10% more than a global one ("global.").
PRICES: dict[str, tuple[float, float]] = {
    "global.anthropic.claude-sonnet-4-6": (3.00, 15.00),
    "us.anthropic.claude-sonnet-4-6": (3.30, 16.50),
    "global.anthropic.claude-haiku-4-5": (1.00, 5.00),
    "us.anthropic.claude-haiku-4-5": (1.10, 5.50),
    "gemini-3.8-flash": (0.75, 3.75),  # through 31 December 2026, then 1.50 and 7.50
    "gemini-3.5-flash-lite": (0.30, 2.50),
}
UNKNOWN_MODEL_PRICE = (5.00, 25.00)  # priced high, so an unknown model hits the cap early

# the model each side switches to partway to the cap
CHEAPER = {
    "global.anthropic.claude-sonnet-4-6": "global.anthropic.claude-haiku-4-5-20251001-v1:0",
    "us.anthropic.claude-sonnet-4-6": "us.anthropic.claude-haiku-4-5-20251001-v1:0",
    "gemini-3.8-flash": "gemini-3.5-flash-lite",
}


def price_for(model: str) -> tuple[float, float]:
    """The longest matching name wins, so a profile prefix picks its own price."""
    best = max((name for name in PRICES if name in model), key=len, default=None)
    return PRICES[best] if best else UNKNOWN_MODEL_PRICE


class BudgetExceeded(RuntimeError):
    pass


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
    _told: bool = field(default=False, repr=False)

    DEFAULT_LIMIT = "5"  # each meter sets its own

    @classmethod
    def from_env(cls, model: str) -> "Budget":
        limit = os.environ.get("LEARNING_BUDGET_USD", cls.DEFAULT_LIMIT)
        cheap = os.environ.get("LEARN_CHEAP_MODEL") or next((c for m, c in CHEAPER.items() if m in model), None)
        return cls(model=model, limit_usd=float(limit) if limit else None,
                   cheap_model=None if cheap == "none" else cheap,
                   switch_at=float(os.environ.get("LEARN_SWITCH_AT", "0.5")))

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

    def current_model(self) -> str:
        """The main model until the switch point, then the cheaper one."""
        if self.cheap_model and self.limit_usd and self.spent_usd >= self.switch_at * self.limit_usd:
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
        """Before a call: refuse it once the course is at its cap."""
        if self.limit_usd is not None and self.spent_usd >= self.limit_usd:
            raise BudgetExceeded(f"spent ${self.spent_usd:.2f} of a ${self.limit_usd:.2f} cap. "
                                 "Raise LEARNING_BUDGET_USD to go further.")
