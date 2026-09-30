"""Counting what a run costs, and stopping it before it costs too much. Strands side.

The usage is already on every agent, in `event_loop_metrics.accumulated_usage`. Two hooks
bolted onto an agent after it exists read it: one before each model call, which refuses the
call once the run is over its cap, and one after, which counts. What a token costs, the
switch to a cheaper model, and the cap itself are shared with ADK, in learning/budget.py.

`BeforeModelCallEvent` has a `cancel` field, and it's the wrong tool for a cap. Cancelling
hands the loop a fake assistant message ("model call denied by hook") with stop reason
end_turn, so a plain call returns that as if the model said it, and a structured call ends
in StructuredOutputException blaming the model. Raising says what actually happened.
"""

from __future__ import annotations

from strands import Agent
from strands.hooks import AfterInvocationEvent, AfterModelCallEvent, BeforeModelCallEvent

from learning.budget import Budget, BudgetExceeded, Usage, price_for  # noqa: F401  (re-exported)


class Meter(Budget):
    DEFAULT_LIMIT = "10"

    def watch(self, agent: Agent, role: str, model: str | None = None) -> Agent:
        """Hooks on an agent that already exists. Returns it, so it chains.

        Each agent's last reading lives in its own hooks. Keying it by id(agent) breaks:
        CPython gives a new agent the id of one already collected, and the new agent
        then starts from the dead one's count. `model` is what this agent runs on, so its
        tokens are priced right after a switch.
        """
        model = model or self.current_model()
        seen = [0, 0]

        def absorb() -> None:
            now = agent.event_loop_metrics.accumulated_usage
            tokens_in, tokens_out = now.get("inputTokens", 0), now.get("outputTokens", 0)
            if (tokens_in, tokens_out) != tuple(seen):
                self.charge(role, tokens_in - seen[0], tokens_out - seen[1], model)
            seen[:] = [tokens_in, tokens_out]

        def before_model_call(event: BeforeModelCallEvent) -> None:
            absorb()
            self.check()

        def after_model_call(event: AfterModelCallEvent) -> None:
            # this fires for failed and refused calls too, so count only real responses
            if event.stop_response is not None:
                self.by_role.setdefault(role, Usage()).calls += 1

        def after_invocation(event: AfterInvocationEvent) -> None:
            absorb()

        agent.add_hook(before_model_call)
        agent.add_hook(after_model_call)
        agent.add_hook(after_invocation)
        return agent
