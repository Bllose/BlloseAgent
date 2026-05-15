import json
from collections.abc import AsyncIterator

from fastapi import APIRouter
from sse_starlette.sse import EventSourceResponse
from langchain_core.messages import HumanMessage

from bllose_agent.models.request import ChatRequest
from bllose_agent.agent.intent.graph import intent_graph

router = APIRouter(prefix="/intent", tags=["intent"])


@router.post("/stream")
async def intent_stream(req: ChatRequest):
    async def event_generator() -> AsyncIterator[dict[str, str]]:
        inputs = {"messages": [HumanMessage(content=req.message)]}

        async for event in intent_graph.astream_events(inputs, version="v2"):
            kind = event["event"]

            if kind == "on_chat_model_stream":
                chunk = event["data"]["chunk"]
                if hasattr(chunk, "content") and chunk.content:
                    yield {
                        "event": "message",
                        "data": json.dumps({"type": "token", "content": chunk.content}),
                    }

        yield {"event": "done", "data": "[DONE]"}

    return EventSourceResponse(event_generator())
