"""The Strands meter, driven through the agent's own hook registry with no model behind it."""

from __future__ import annotations

import asyncio
import gc

import pytest
from strands import Agent
from strands.hooks import AfterInvocationEvent, BeforeModelCallEvent

from impl.strands.telemetry import BudgetExceeded, Meter


def finish(agent: Agent, tokens_in: int, tokens_out: int) -> None:
    """What an invocation leaves behind: usage on the agent, then the after-invocation hook."""
    agent.event_loop_metrics.accumulated_usage.update(inputTokens=tokens_in, outputTokens=tokens_out)
    asyncio.run(agent.hooks.invoke_callbacks_async(AfterInvocationEvent(agent=agent, invocation_state={})))


def test_every_agent_counts_from_zero_even_when_python_reuses_its_id():
    # one Agent per call, thrown away after, and CPython hands a new object the id of a
    # dead one. A run once reported -834706 input tokens for a role because of it.
    meter = Meter()
    for _ in range(30):
        agent = Agent(callback_handler=None)
        meter.watch(agent, "extract")
        finish(agent, 1000, 100)
        del agent
        gc.collect()
    assert meter.by_role["extract"].input_tokens == 30_000
    assert meter.by_role["extract"].output_tokens == 3_000


def test_one_agent_asked_twice_is_counted_once_per_token():
    meter = Meter()
    agent = meter.watch(Agent(callback_handler=None), "review")
    finish(agent, 1000, 100)
    finish(agent, 2500, 300)   # accumulated usage only grows
    assert (meter.by_role["review"].input_tokens, meter.by_role["review"].output_tokens) == (2500, 300)


def test_the_cap_refuses_the_next_call_once_the_run_is_over_it():
    meter = Meter(model="global.anthropic.claude-sonnet-4-6", limit_usd=0.01)
    first = meter.watch(Agent(callback_handler=None), "extract")
    finish(first, 3000, 100)                 # $0.0105, over the cap
    second = meter.watch(Agent(callback_handler=None), "curriculum")
    with pytest.raises(BudgetExceeded):
        asyncio.run(second.hooks.invoke_callbacks_async(
            BeforeModelCallEvent(agent=second, invocation_state={})))
