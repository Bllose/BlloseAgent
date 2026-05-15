from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode

from bllose_agent.agent.state import AgentState
from bllose_agent.agent.nodes import agent_node, should_continue
from bllose_agent.tools.base import TOOLS


def build_graph() -> StateGraph:
    graph = StateGraph(AgentState)

    graph.add_node("agent", agent_node)
    graph.add_node("tools", ToolNode(TOOLS))

    graph.set_entry_point("agent")
    graph.add_conditional_edges("agent", should_continue, {
        "tools": "tools",
        "__end__": END,
    })
    graph.add_edge("tools", "agent")

    return graph.compile()


agent_graph = build_graph()
