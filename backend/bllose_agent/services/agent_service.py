import json
from collections.abc import AsyncIterator

from langchain_core.messages import HumanMessage

from bllose_agent.services.team_manager import BUS, get_self_agent


def _classify(content) -> tuple[str, str]:
    """Return (event_type, extracted_text) for a chunk of LLM content."""
    if isinstance(content, str):
        return ("text", content)
    if isinstance(content, list):
        for block in content:
            if isinstance(block, dict):
                if block.get("type") == "thinking":
                    return ("thinking", str(block.get("thinking", "")))
                if "text" in block:
                    return ("text", str(block["text"]))
    return ("text", str(content))


class AgentService:
    """Multi-agent service — bllose is the intent-recognition lead agent.

    bllose interacts with the user, uses file/shell tools, and
    coordinates with expert teammates (Coding Leader, Paper Leader)
    through self_agent.  Expert lifecycle is managed by SelfAgent.
    """

    def __init__(self):
        # SelfAgent must already be running (started in FastAPI lifespan)
        self._self_agent = get_self_agent()

    async def run_stream(self, message: str) -> AsyncIterator[dict]:
        """Run the bllose agent graph and yield streaming events."""
        bllose = self._self_agent.get_agent("bllose")
        if bllose is None:
            yield {"type": "error", "content": "bllose agent not running"}
            return

        # Drain inbox before processing — teammate/self_agent replies
        inbox = BUS.read_inbox("bllose")
        messages: list = [HumanMessage(content=message)]
        if inbox:
            messages.insert(0, HumanMessage(
                content=f"<inbox>{json.dumps(inbox, indent=2)}</inbox>"
            ))

        bllose.set_status("working")

        inputs = {"messages": messages}
        async for event in bllose.graph.astream_events(inputs, version="v2"):
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

        bllose.set_status("idle")
