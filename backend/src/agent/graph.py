from langgraph.graph import StateGraph, END

from src.agent.state import AgentState
from src.agent.nodes import chat_node


def build_graph() -> StateGraph:
    graph = StateGraph(AgentState)

    graph.add_node("chat", chat_node)
    graph.set_entry_point("chat")
    graph.add_edge("chat", END)

    return graph.compile()


agent_graph = build_graph()
