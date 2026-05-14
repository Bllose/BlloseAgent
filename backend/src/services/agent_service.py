from collections.abc import AsyncIterator

from langchain_core.messages import HumanMessage

from src.agent.graph import agent_graph


def _classify(content) -> tuple[str, str]:
    """Return (event_type, extracted_text) for a chunk of LLM content."""
    if isinstance(content, str):
        return ("text", content)
    if isinstance(content, list):
        for block in content:
            if isinstance(block, dict):
                if block.get("type") == "thinking":
                    # thinking 块有两种：正文（thinking 字段）和结束标记（signature 字段）
                    # signature 块无实际文本，返回空串，前端自动跳过
                    return ("thinking", str(block.get("thinking", "")))
                if "text" in block:
                    return ("text", str(block["text"]))
    return ("text", str(content))


class AgentService:
    async def run_stream(self, message: str) -> AsyncIterator[dict]:
        """Run the LangGraph agent and yield streaming events."""
        inputs = {"messages": [HumanMessage(content=message)]}

        async for event in agent_graph.astream_events(inputs, version="v2"):
            kind = event["event"]

            if kind == "on_chat_model_stream":
                chunk = event["data"]["chunk"]
                if hasattr(chunk, "content") and chunk.content:
                    event_type, text = _classify(chunk.content)
                    yield {"type": event_type, "content": text}

            elif kind == "on_tool_start":
                yield {
                    "type": "tool_start",
                    "name": event["name"],
                }

            elif kind == "on_tool_end":
                yield {
                    "type": "tool_end",
                    "name": event["name"],
                    "output": str(event["data"].get("output", "")),
                }
