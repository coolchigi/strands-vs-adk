"""Part 1, Where does state live: Strands agent.state.

This one needs no credentials. It only touches the state object, so it is the
quickest way to prove your install works.
"""
from strands import Agent

agent = Agent()

agent.state.set("course_topic", "Building AI agents")

print(agent.state.get("course_topic"))

agent.state.delete("course_topic")

print(agent.state.get("course_topic"))
