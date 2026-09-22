"""Part 1, Observability: the metrics Strands hands back on every result.

Run:  python observe_strands.py

Strands puts an EventLoopMetrics object on the AgentResult, so instrumentation is
a read off the thing you already have. ADK gives you a stream of events instead,
with usage on event.usage_metadata, so you either watch events go past or
register after_model_callback at construction.
"""
from strands import Agent, tool


@tool
def get_course_topic() -> str:
    """Get the topic for the course."""
    return "Building AI agents"


agent = Agent(tools=[get_course_topic])

result = agent("Name one lesson about the course topic. One line.")

# Strands streams the answer to stdout as it arrives, without a trailing newline,
# so start a fresh line before printing anything of our own.
print()

print(f"Total tokens: {result.metrics.accumulated_usage['totalTokens']}")
print(f"Execution time: {sum(result.metrics.cycle_durations):.2f} seconds")
print(f"Tools used: {list(result.metrics.tool_metrics.keys())}")

# Everything above, plus cycle counts and traces, in one dict.
print(result.metrics.get_summary())
