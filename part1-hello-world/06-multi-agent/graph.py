"""Part 1, What if one agent isn't enough: the Strands Graph.

Run:  python graph.py

The revision path is a conditional edge, added before build() and bounded by
set_max_node_executions. build() snapshots the edges, so an edge added after it never
reaches the graph. Hit the execution cap and the graph ends FAILED.

Note what these agents do NOT have: each other in `tools`. Agents as tools and a
graph are two ways to connect agents, not two layers of the same one. Wire both and
every node can rerun the whole chain below it through its tools, and a second call to
an agent that is already running is refused:

    tool_name=<researcher>, tool_use_id=<...> | agent is already processing a request

That goes back to the calling model as a tool error, and it asks again.
"""
from strands import Agent
from strands.multiagent import GraphBuilder

researcher = Agent(
    name="researcher",
    system_prompt="Find information from official documentation, blogs, and other reliable sources.",
)

curriculum_builder = Agent(
    name="curriculum_builder",
    system_prompt="Turn the research into a structured curriculum.",
)

teacher = Agent(
    name="teacher",
    system_prompt="Create lessons from the curriculum.",
)

feedback = Agent(
    name="feedback",
    system_prompt=(
        "Review the lesson. Reply 'looks good' if it teaches the topic clearly, "
        "or 'revise the lesson' with one reason if it does not."
    ),
)


def lesson_needs_work(state) -> bool:
    result = state.results["feedback"].result
    return "revise the lesson" in str(result).lower()


builder = GraphBuilder()

builder.add_node(researcher, "researcher")
builder.add_node(curriculum_builder, "curriculum")
builder.add_node(teacher, "teacher")
builder.add_node(feedback, "feedback")

builder.add_edge("researcher", "curriculum")
builder.add_edge("curriculum", "teacher")
builder.add_edge("teacher", "feedback")
builder.add_edge("feedback", "teacher", condition=lesson_needs_work)

builder.set_entry_point("researcher")
builder.set_max_node_executions(10)
builder.reset_on_revisit(True)

graph = builder.build()

if __name__ == "__main__":
    result = graph("Teach me about photosynthesis.")
    print(f"\n=== {result.status} ===")
