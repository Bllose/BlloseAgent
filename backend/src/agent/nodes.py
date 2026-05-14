from src.agent.state import AgentState
from src.config.settings import settings


async def chat_node(state: AgentState) -> dict:
    llm = settings.get_llm(streaming=True)
    messages = state["messages"]
    response = await llm.ainvoke(messages)
    return {"messages": [response]}
