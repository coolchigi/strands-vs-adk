"""Part 1, What runs the agent loop: ADK's Runner.

Run:  python main.py            (from the 03_agent_loop folder)
Needs GOOGLE_API_KEY in course_agent/.env, or exported in your shell.

Strands runs the loop when you call the agent. ADK gives you a Runner, a session
service and a stream of events, which is the whole point of this file.
"""
import asyncio

from course_agent.agent import root_agent
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types

session_service = InMemorySessionService()

runner = Runner(
    app_name="course_agent",
    agent=root_agent,
    session_service=session_service,
)


async def main():
    session = await session_service.create_session(
        app_name="course_agent",
        user_id="user",
    )

    message = types.Content(
        role="user",
        parts=[types.Part(text="What topic should I teach?")],
    )

    async for event in runner.run_async(
        user_id="user",
        session_id=session.id,
        new_message=message,
    ):
        if event.is_final_response():
            # is_final_response() is True for error events too, and those carry
            # no content. Print it unguarded and a bad key reaches you as
            # AttributeError: 'NoneType' object has no attribute 'parts'.
            if event.content:
                print(event.content.parts[0].text)
            else:
                print(f"no content: {event.error_message}")


asyncio.run(main())
