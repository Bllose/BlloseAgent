from langgraph.graph import StateGraph, END

from bllose_agent.agent.intent.state import IntentAgentState
from bllose_agent.agent.intent.nodes import classify_intent_node, handle_intent_node


def build_intent_graph() -> StateGraph:
    graph = StateGraph(IntentAgentState)

    graph.add_node("classify", classify_intent_node)
    graph.add_node("handle", handle_intent_node)

    graph.set_entry_point("classify")
    graph.add_edge("classify", "handle")
    graph.add_edge("handle", END)

    return graph.compile()


intent_graph = build_intent_graph()
