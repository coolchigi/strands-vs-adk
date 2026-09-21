"""Part 1, Deployment: wrapping a Strands agent in FastAPI.

Install:  pip install fastapi uvicorn
Run:      uvicorn app:app --reload

Strands ships A2AServer for exposing one agent over the A2A protocol, and no
deploy command. ADK ships `adk deploy` with four targets. For an ordinary HTTP
API this is the whole job.
"""
from fastapi import FastAPI
from strands import Agent

app = FastAPI()

agent = Agent(system_prompt="You are a helpful certification teacher.")


@app.post("/ask")
def ask(question: str):
    result = agent(question)
    return {"response": str(result.message)}
