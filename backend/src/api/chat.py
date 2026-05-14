import json
from collections.abc import AsyncIterator

from fastapi import APIRouter
from sse_starlette.sse import EventSourceResponse

from src.models.request import ChatRequest
from src.services.agent_service import AgentService

router = APIRouter(prefix="/chat", tags=["chat"])


@router.post("/stream")
async def chat_stream(req: ChatRequest):
    service = AgentService()

    async def event_generator() -> AsyncIterator[dict[str, str]]:
        async for event in service.run_stream(req.message):
            sse_event = event.get("type", "message")
            yield {"event": sse_event, "data": json.dumps(event)}

        yield {"event": "done", "data": "[DONE]"}

    return EventSourceResponse(event_generator())
