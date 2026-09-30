"""The run's command line: the budget holds across restarts, and a cap stop is a clean stop."""

from __future__ import annotations

from impl.strands.telemetry import BudgetExceeded, Meter, Usage
from learning import cli
from learning.model import LearnerProfile

SONNET = "global.anthropic.claude-sonnet-4-6"


def run(tmp_path, pipeline, meter):
    runs = tmp_path / "runs"
    runs.mkdir(exist_ok=True)
    (runs / "profile.json").write_text(LearnerProfile(subject="Terraform", goal="x", subject_is_clear=True)
                                       .model_dump_json())
    return cli.main("strands", "m", lambda m: None, meter, pipeline, BudgetExceeded,
                    ["learn Terraform", "--runs", str(runs), "--out", str(tmp_path / "out")])


def spends(role, tokens_in):
    def pipeline(flow):
        flow_meter.charge(role, tokens_in, 0)
        raise RuntimeError("the model call failed") from BudgetExceeded("over the cap")
    return pipeline


def test_a_restarted_run_starts_from_what_it_already_spent(tmp_path):
    global flow_meter
    flow_meter = Meter(model=SONNET, limit_usd=25)
    assert run(tmp_path, spends("research", 1_000_000), flow_meter) == 2
    flow_meter = Meter(model=SONNET, limit_usd=25)    # a new process, a new meter
    run(tmp_path, spends("curriculum", 1_000_000), flow_meter)
    assert flow_meter.spent_usd == 6.0


def test_a_budget_stop_wrapped_by_the_framework_is_still_a_budget_stop(tmp_path, capsys):
    global flow_meter
    flow_meter = Meter()
    assert run(tmp_path, spends("x", 1), flow_meter) == 2
    assert "Stopped by the budget cap" in capsys.readouterr().err


def test_spend_is_on_disk_as_soon_as_it_is_counted(tmp_path):
    # a killed run never reaches `finally`, so what it spent has to be written as it goes
    import asyncio
    from types import SimpleNamespace

    from strands import Agent
    from strands.hooks import AfterInvocationEvent

    from impl.adk.telemetry import Meter as AdkMeter

    def pipeline(flow):
        agent = strands_meter.watch(Agent(callback_handler=None), "extract")
        agent.event_loop_metrics.accumulated_usage.update(inputTokens=500, outputTokens=50)
        asyncio.run(agent.hooks.invoke_callbacks_async(AfterInvocationEvent(agent=agent, invocation_state={})))
        seen.append((tmp_path / "runs" / "spend.json").read_text())
        raise RuntimeError("killed") from BudgetExceeded("x")

    strands_meter, seen = Meter(), []
    run(tmp_path, pipeline, strands_meter)
    assert '500' in seen[0]

    adk_meter, calls = AdkMeter(), []
    adk_meter.persist = lambda: calls.append(adk_meter.total.input_tokens)
    after = adk_meter.callbacks("lesson")["after_model_callback"]
    after(llm_response=SimpleNamespace(usage_metadata=SimpleNamespace(
        prompt_token_count=700, candidates_token_count=10, thoughts_token_count=5)))
    assert calls == [700]
