from langchain_core.messages import HumanMessage, SystemMessage

from src.agent.intent.state import IntentAgentState
from src.config.settings import settings

INTENT_PROMPT = """Analyze the user's message and classify it into exactly one of these intents:

- greeting: casual hello, hi, how are you, good morning, etc.
- question: asking for information, explanation, or help
- command: requesting an action or task to be performed
- other: anything that doesn't fit the above

Reply with ONLY the intent label, nothing else."""

HANDLER_PROMPTS = {
    "greeting": "You are BlloseAgent. Reply with a warm and friendly greeting. Keep it short.",
    "question": "You are BlloseAgent, a helpful AI assistant. Answer the user's question thoroughly and accurately.",
    "command": "You are BlloseAgent, an AI agent capable of executing tasks. Acknowledge the user's request and explain that you'll help them accomplish it.",
    "other": "You are BlloseAgent, a helpful AI assistant. Respond naturally to the user's message.",
}


async def classify_intent_node(state: IntentAgentState) -> dict:
    llm = settings.get_llm()
    messages = [SystemMessage(content=INTENT_PROMPT), state["messages"][-1]]
    response = await llm.ainvoke(messages)
    raw = response.content.strip().lower() if hasattr(response, "content") else str(response).strip().lower()

    valid = {"greeting", "question", "command"}
    intent = raw if raw in valid else "other"
    return {"intent": intent}


async def handle_intent_node(state: IntentAgentState) -> dict:
    intent = state.get("intent", "other")
    system_prompt = HANDLER_PROMPTS.get(intent, HANDLER_PROMPTS["other"])

    llm = settings.get_llm(streaming=True)
    messages = [SystemMessage(content=system_prompt)] + list(state["messages"])
    response = await llm.ainvoke(messages)
    return {"messages": [response]}
