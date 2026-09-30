"""A typed answer from a Strands agent.

Run:  python examples/structured_strands.py      (needs AWS credentials with Bedrock access)
"""
from pydantic import BaseModel
from strands import Agent


class Question(BaseModel):
    stem: str
    options: list[str]
    answer: int  # index into options
    explanation: str


agent = Agent(system_prompt="You write quiz questions about Terraform.", callback_handler=None)
result = agent("One question on what terraform init does.", structured_output_model=Question)

question = result.structured_output
print(type(question).__name__)
print(question.stem)
print(question.options[question.answer])
