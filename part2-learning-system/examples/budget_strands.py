"""A spending cap on a Strands agent, bolted on after the agent exists.

Run:  python examples/budget_strands.py      (needs AWS credentials with Bedrock access)

The cap here is a tenth of a cent, so the second question never reaches the model.
"""
from strands import Agent
from strands.hooks import BeforeModelCallEvent

PRICE = (3.00, 15.00)  # USD per million tokens, in and out, for Claude Sonnet 4.6
CAP = 0.001


class BudgetExceeded(RuntimeError):
    pass


def spent(agent: Agent) -> float:
    usage = agent.event_loop_metrics.accumulated_usage
    return (usage["inputTokens"] * PRICE[0] + usage["outputTokens"] * PRICE[1]) / 1_000_000


def enforce_cap(event: BeforeModelCallEvent) -> None:
    if spent(event.agent) >= CAP:
        raise BudgetExceeded(f"spent ${spent(event.agent):.4f}, the cap is ${CAP}")


agent = Agent(system_prompt="Answer in one short paragraph.", callback_handler=None)
agent.add_hook(enforce_cap)

print(agent("What does terraform init do?"))
print(f"spent ${spent(agent):.4f}")
try:
    print(agent("And terraform plan?"))
except BudgetExceeded as e:
    print("stopped:", e)
