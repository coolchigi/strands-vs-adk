"""The revision loop on an ADK Workflow, with stages that are ordinary Python.

Run:  python examples/loop_adk.py      (no model, no keys)

Any function is a node. The loop is a routed edge from the router back to teaching.
ADK does not bound a routed cycle, so the router is what stops it.
"""
import asyncio

from google.adk import Event, Workflow
from google.adk.runners import InMemoryRunner
from google.genai import types

board = {"reviews": 0, "verdict": None}
MAX_REVIEWS = 4


async def teaching() -> None:
    # nodes run on the workflow's event loop, and real stages block, so off it they go
    await asyncio.to_thread(print, "teaching")


def feedback() -> None:
    board["reviews"] += 1
    board["verdict"] = "revise" if board["reviews"] < 3 else "approved"
    print(f"review {board['reviews']}: {board['verdict']}")


def route() -> Event:
    if board["verdict"] == "approved" or board["reviews"] >= MAX_REVIEWS:
        return Event(route="stop")
    return Event(route="revise")


def stop() -> None:
    return None


root_agent = Workflow(name="revision_loop", edges=[
    ("START", teaching, feedback, route),
    (route, {"revise": teaching, "stop": stop}),
])


async def main() -> None:
    runner = InMemoryRunner(agent=root_agent, app_name="loop")
    session = await runner.session_service.create_session(app_name="loop", user_id="me")
    message = types.Content(role="user", parts=[types.Part(text="build the course")])
    async for _ in runner.run_async(user_id="me", session_id=session.id, new_message=message):
        pass


if __name__ == "__main__":
    asyncio.run(main())
