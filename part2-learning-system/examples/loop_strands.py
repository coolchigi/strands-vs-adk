"""The revision loop on a Strands Graph, with stages that are ordinary Python.

Run:  python examples/loop_strands.py      (no model, no keys)

A graph node has to be an Agent or a MultiAgentBase, so a stage of plain code gets a
small subclass. The loop is a conditional edge, and set_max_node_executions stops it.
"""
import asyncio

from strands.multiagent import GraphBuilder
from strands.multiagent.base import MultiAgentBase, MultiAgentResult, Status

board = {"reviews": 0, "verdict": None}


class Stage(MultiAgentBase):
    def __init__(self, name, work):
        super().__init__()
        self.name = name
        self.work = work

    async def invoke_async(self, task, invocation_state=None, **kwargs):
        # the graph runs nodes on its event loop, and real stages block, so off it they go
        await asyncio.to_thread(self.work)
        # results stays empty: Strands walks into it to build the next node's input,
        # so it has to be real results or nothing
        return MultiAgentResult(status=Status.COMPLETED, results={})


def teach():
    print("teaching")


def review():
    board["reviews"] += 1
    board["verdict"] = "revise" if board["reviews"] < 3 else "approved"
    print(f"review {board['reviews']}: {board['verdict']}")


builder = GraphBuilder()
builder.add_node(Stage("teaching", teach), "teaching")
builder.add_node(Stage("feedback", review), "feedback")
builder.add_edge("teaching", "feedback")
builder.add_edge("feedback", "teaching", condition=lambda state: board["verdict"] == "revise")
builder.set_entry_point("teaching")
builder.set_max_node_executions(10)
builder.reset_on_revisit(True)
graph = builder.build()

if __name__ == "__main__":
    result = graph("build the course")
    print(result.status)
