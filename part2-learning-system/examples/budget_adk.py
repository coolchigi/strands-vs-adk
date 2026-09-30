"""A spending cap on an ADK agent, passed in when the agent is built.

Run:  export GOOGLE_API_KEY=...  then  python examples/budget_adk.py

The cap here is a hundredth of a cent, so the second question never reaches the model.
ADK hands the exception back twice: first as an error event, then raised when the
stream ends.
"""
import asyncio

from google.adk.agents import Agent
from google.adk.runners import InMemoryRunner
from google.genai import types

PRICE = (0.75, 3.75)  # USD per million tokens, in and out, for Gemini 3.8 Flash
CAP = 0.0001
tokens = {"in": 0, "out": 0}


class BudgetExceeded(RuntimeError):
    pass


def spent() -> float:
    return (tokens["in"] * PRICE[0] + tokens["out"] * PRICE[1]) / 1_000_000


def enforce_cap(callback_context, llm_request):
    if spent() >= CAP:
        raise BudgetExceeded(f"spent ${spent():.6f}, the cap is ${CAP}")


def count(callback_context, llm_response):
    usage = llm_response.usage_metadata
    if usage:
        tokens["in"] += usage.prompt_token_count or 0
        # thinking tokens are billed as output and reported separately
        tokens["out"] += (usage.candidates_token_count or 0) + (usage.thoughts_token_count or 0)


agent = Agent(
    name="tutor",
    model="gemini-3.8-flash",
    instruction="Answer in one short paragraph.",
    before_model_callback=enforce_cap,
    after_model_callback=count,
)


async def ask(runner, session_id, text):
    message = types.Content(role="user", parts=[types.Part(text=text)])
    async for event in runner.run_async(user_id="me", session_id=session_id, new_message=message):
        if event.error_code:
            print("error event:", event.error_code)
        elif event.is_final_response():
            print(event.content.parts[0].text)


async def main():
    runner = InMemoryRunner(agent=agent, app_name="tutor")
    session = await runner.session_service.create_session(app_name="tutor", user_id="me")
    await ask(runner, session.id, "What does terraform init do?")
    print(f"spent ${spent():.6f}")
    try:
        await ask(runner, session.id, "And terraform plan?")
    except BudgetExceeded as e:
        print("stopped:", e)


asyncio.run(main())
