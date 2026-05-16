import json
from collections.abc import AsyncIterator

from langchain_core.messages import HumanMessage, ToolMessage

from bllose_agent.services.team_manager import BUS, get_self_agent
from bllose_agent.services.token_tracker import serialize_message


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

        output_actual = 0
        all_input = 0
        all_output = 0
        output_text = ""
        graph_snapshot: list[dict] = []

        # Record the initial user message in the graph snapshot
        for m in messages:
            graph_snapshot.append(serialize_message(m))

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
                        if result[0] == "text":
                            output_text += result[1]

            elif kind == "on_chat_model_end":
                output = event["data"].get("output")
                if hasattr(output, "usage_metadata"):
                    um = output.usage_metadata
                    # User-facing: keep the last response's output tokens
                    output_actual = um.get("output_tokens", 0)
                    # All-in/all-out: accumulate every LLM call
                    all_input += um.get("input_tokens", 0)
                    all_output += um.get("output_tokens", 0)
                # Capture the full AI message
                if output is not None:
                    graph_snapshot.append(serialize_message(output))

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
                # Reconstruct a ToolMessage for the graph snapshot
                tool_msg = ToolMessage(
                    content=str(event["data"].get("output", "")),
                    name=event["name"],
                    tool_call_id="",
                )
                graph_snapshot.append(serialize_message(tool_msg))

        # Record this turn's token usage
        tracker.record(
            input_est,
            output_actual,
            all_input=all_input,
            all_output=all_output,
            input_text=message,
            output_text=output_text,
            graph_messages=graph_snapshot,
        )

        bllose.set_status("idle")
