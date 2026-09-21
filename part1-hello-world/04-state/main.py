"""Part 1, Where does state live: ADK keeps it in a Session.

Run:  python main.py            (from the 04_state folder)

Session state is seeded at creation and read back off the session. The agent's
instruction templates {course_topic} straight out of it.
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
        state={"course_topic": "Building AI agents"},
    )

    print(session.state["course_topic"])

    message = types.Content(
        role="user",
        parts=[types.Part(text="What should the first lesson cover?")],
    )

    async for event in runner.run_async(
        user_id="user",
        session_id=session.id,
        new_message=message,
    ):
        if event.is_final_response():
            if event.content:
                print(event.content.parts[0].text)
            else:
                print(f"no content: {event.error_message}")


asyncio.run(main())
