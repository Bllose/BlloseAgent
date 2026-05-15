from fastapi import APIRouter

from bllose_agent.models.response import AgentInfoResponse
from bllose_agent.config.settings import settings

router = APIRouter(prefix="/agent", tags=["agent"])


@router.get("/info", response_model=AgentInfoResponse)
async def get_agent_info():
    return AgentInfoResponse(
        name="BlloseAgent",
        version="0.1.0",
        model=settings.llm_model,
    )
