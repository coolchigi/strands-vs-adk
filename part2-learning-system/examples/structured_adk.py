"""A typed answer from an ADK agent.

Run:  python examples/structured_adk.py      (needs GOOGLE_API_KEY)
"""
import asyncio

from google.adk.agents import Agent
from google.adk.runners import InMemoryRunner
from google.genai import types
from pydantic import BaseModel


class Question(BaseModel):
    stem: str
    options: list[str]
    answer: int  # index into options
    explanation: str


agent = Agent(
    name="quiz",
    model="gemini-3.8-flash",
    instruction="You write quiz questions about Terraform.",
    output_schema=Question,
    output_key="question",
)


async def main() -> None:
    runner = InMemoryRunner(agent=agent, app_name="quiz")
    session = await runner.session_service.create_session(app_name="quiz", user_id="me")
    message = types.Content(role="user", parts=[types.Part(text="One question on what terraform init does.")])
    async for _ in runner.run_async(user_id="me", session_id=session.id, new_message=message):
        pass
    done = await runner.session_service.get_session(app_name="quiz", user_id="me", session_id=session.id)
    raw = done.state["question"]
    print(type(raw).__name__)
    question = Question.model_validate(raw)
    print(question.stem)
    print(question.options[question.answer])


asyncio.run(main())
