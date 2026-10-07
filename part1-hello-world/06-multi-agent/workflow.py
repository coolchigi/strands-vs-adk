"""Part 1, What if one agent isn't enough: ADK's Workflow, with the revision loop.

Run:  export GOOGLE_API_KEY=...  then  python workflow.py

The loop is a routed back-edge: `review` returns a route, and "revise" points back at
`teacher`. ADK rejects a cycle with no routed edge in it when the Workflow is built,
and it does not bound a routed one. The `rounds` counter is what ends this loop.

Workflow lives at google.adk.Workflow, not google.adk.agents. These agents have no
`sub_agents`: with that wiring left in, the model can hand control to another agent
mid-run and a node runs twice or the workflow stops early.

An agent in a Workflow only sees what the node before it hands over (ADK runs it in
single_turn mode). On a revision, `review` hands `teacher` the feedback, so on its own
the teacher never sees the lesson it's revising and writes a new one, sometimes on a
different topic. `output_key="lesson"` saves the lesson in session state, the `lesson`
parameter on `review` reads it back, and the revise route carries both.
"""
import asyncio

from google.adk import Event, Workflow
from google.adk.agents import Agent
from google.adk.runners import InMemoryRunner
from google.genai import types

researcher = Agent(
    name="researcher",
    model="gemini-flash-latest",
    instruction="In three short bullet points, say what photosynthesis is. No preamble.",
)
curriculum_builder = Agent(
    name="curriculum_builder",
    model="gemini-flash-latest",
    instruction="Turn the research into a two item lesson plan. No preamble.",
)
teacher = Agent(
    name="teacher",
    model="gemini-flash-latest",
    instruction="Write the first lesson from the plan in two sentences. If feedback asks for a change, make it.",
    output_key="lesson",
)
feedback = Agent(
    name="feedback",
    model="gemini-flash-latest",
    instruction=(
        "Review the lesson. If it does not use the word chlorophyll, reply exactly "
        "'revise the lesson: mention chlorophyll'. Otherwise reply exactly 'looks good'."
    ),
)

rounds = {"n": 0}


def review(node_input: str, lesson: str) -> Event:
    rounds["n"] += 1
    if "revise the lesson" in node_input.lower() and rounds["n"] < 3:
        return Event(route="revise", output=f"Your lesson: {lesson}\nFeedback: {node_input}")
    return Event(route="done", output=node_input)


def finish(node_input: str) -> str:
    return node_input


root_agent = Workflow(
    name="learning_system",
    edges=[
        ("START", researcher, curriculum_builder, teacher, feedback, review),
        (review, {"revise": teacher, "done": finish}),
    ],
)


async def main() -> None:
    runner = InMemoryRunner(agent=root_agent, app_name="learning_system")
    session = await runner.session_service.create_session(app_name="learning_system", user_id="me")
    message = types.Content(role="user", parts=[types.Part(text="Teach me photosynthesis.")])
    async for event in runner.run_async(user_id="me", session_id=session.id, new_message=message):
        if event.content and event.content.parts and event.content.parts[0].text:
            print(f"[{event.author}] {event.content.parts[0].text.strip()[:90]}")
    print("feedback rounds:", rounds["n"])


if __name__ == "__main__":
    asyncio.run(main())
