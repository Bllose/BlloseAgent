from typing import Annotated, TypedDict, Literal

from langgraph.graph.message import add_messages


class IntentAgentState(TypedDict):
    messages: Annotated[list, add_messages]
    intent: str
