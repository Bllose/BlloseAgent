import json
from collections.abc import AsyncIterator

from langchain_core.messages import HumanMessage

from bllose_agent.services.team_manager import BUS, get_self_agent


def _classify(content) -> tuple[str, str] | None:
    """Return (event_type, extracted_text) for a chunk of LLM content.

    Returns None for tool-call internals (tool_use, input_json_delta) —
    those are surfaced via on_tool_start / on_tool_end events instead.
    """
    if isinstance(content, str):
        return ("text", content)
    if isinstance(content, list):
        for block in content:
            if isinstance(block, dict):
                block_type = block.get("type", "")
                if block_type == "thinking":
                    return ("thinking", str(block.get("thinking", "")))
                if block_type == "text":
                    return ("text", str(block.get("text", "")))
    return None


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

        # Estimate input tokens before the call
        tracker = self._self_agent.token_tracker.agent("bllose")
        input_est = tracker.estimate(messages)

        bllose.set_status("working")

        output_tokens = 0

        inputs = {"messages": messages}
        async for event in bllose.graph.astream_events(
            inputs, version="v2",
            config={"recursion_limit": 100},
        ):
            kind = event["event"]

            if kind == "on_chat_model_stream":
                chunk = event["data"]["chunk"]
                if hasattr(chunk, "content") and chunk.content:
                    result = _classify(chunk.content)
                    if result is not None:
                        yield {"type": result[0], "content": result[1]}

            elif kind == "on_chat_model_end":
                output = event["data"].get("output")
                if hasattr(output, "usage_metadata"):
                    output_tokens += output.usage_metadata.get(
                        "output_tokens", 0
                    )

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

        # Record this turn's token usage
        tracker.record(input_est, output_tokens)

        bllose.set_status("idle")
