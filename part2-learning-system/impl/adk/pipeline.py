"""The run as an ADK Workflow.

Stages and reviews are nodes. Each review is a function returning an Event whose route
names the next node, so the feedback loop is routed edges in the graph. ADK rejects a
cycle with no routed edge in it when the Workflow is built, and doesn't bound a routed
one. The flow stops retrying a stage after a few attempts, which is what ends the loop.

Any function can be a node. The stages block and call agents with their own event loops,
so they run in a worker thread.
"""

from __future__ import annotations

import asyncio

from google.adk import Event, Workflow
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types

from learning.flow import CURRICULUM, DONE, RESEARCH, TEACHING, Flow

from .telemetry import raise_for


def build_workflow(flow: Flow) -> Workflow:
    async def research() -> None:
        await asyncio.to_thread(flow.research)

    async def review_research() -> Event:
        return Event(route=await asyncio.to_thread(flow.review_research))

    async def curriculum() -> None:
        await asyncio.to_thread(flow.curriculum)

    async def review_curriculum() -> Event:
        return Event(route=await asyncio.to_thread(flow.review_curriculum))

    async def teaching() -> None:
        await asyncio.to_thread(flow.teaching)

    async def review_teaching() -> Event:
        flow.board.route = await asyncio.to_thread(flow.review_teaching)
        return Event(route=flow.board.route)

    def done() -> None:
        return None

    return Workflow(name="learning_system", edges=[
        ("START", research, review_research),
        (review_research, {RESEARCH: research, CURRICULUM: curriculum}),
        (curriculum, review_curriculum),
        (review_curriculum, {RESEARCH: research, CURRICULUM: curriculum, TEACHING: teaching}),
        (teaching, review_teaching),
        (review_teaching, {DONE: done}),
    ])


async def _run(flow: Flow) -> None:
    sessions = InMemorySessionService()
    runner = Runner(app_name="learning_system", agent=build_workflow(flow), session_service=sessions)
    session = await sessions.create_session(app_name="learning_system", user_id="learner")
    message = types.Content(role="user", parts=[types.Part(text="build the course")])
    async for event in runner.run_async(user_id="learner", session_id=session.id, new_message=message):
        raise_for(event, "the workflow")


def run(flow: Flow) -> None:
    asyncio.run(_run(flow))
    if flow.board.route != DONE:
        raise RuntimeError(f"the workflow stopped at {flow.board.route}")
