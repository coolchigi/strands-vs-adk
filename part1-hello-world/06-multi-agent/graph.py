"""Part 1, What if one agent isn't enough: the Strands Graph.

Run:  python graph.py

The revision path is a conditional edge, declared up front and bounded by
set_max_node_executions. ADK graph workflows branch but do not loop.
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
    tools=[researcher],
)

teacher = Agent(
    name="teacher",
    system_prompt="Create lessons from the curriculum.",
    tools=[curriculum_builder],
)

feedback = Agent(
    name="feedback",
    system_prompt="Review the research, curriculum, and lessons.",
    tools=[teacher],
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

graph = builder.build()

if __name__ == "__main__":
    graph("Teach me about photosynthesis.")
