"""Part 1, Deployment: wrapping a Strands agent in FastAPI.

Install:  pip install strands-agents fastapi uvicorn
Run:      uvicorn app:app --reload
Try:      curl -X POST localhost:8000/ask -H 'content-type: application/json' \\
               -d '{"question": "What is Amazon Bedrock?"}'

One agent per request. An Agent holds its own conversation, so a shared one would mix
every caller's messages, and Strands refuses a second call while one is running.
str(result) is the answer's text. result.message is the whole message dict.

Strands ships A2AServer for exposing one agent over the A2A protocol, and no deploy
command. ADK ships `adk deploy` with four targets. For an ordinary HTTP API this is the
whole job.
"""
from fastapi import FastAPI
from pydantic import BaseModel
from strands import Agent

app = FastAPI()


class Question(BaseModel):
    question: str


@app.post("/ask")
def ask(body: Question):
    agent = Agent(system_prompt="You are a helpful certification teacher.")
    result = agent(body.question)
    return {"response": str(result)}
