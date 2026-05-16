from fastapi import APIRouter

from bllose_agent.models.response import (
    AgentHistoryResponse,
    AgentInfoResponse,
    AgentStatusResponse,
    TokenStatsResponse,
    GlobalTokenStatsResponse,
    TurnRecord,
)
from bllose_agent.config.settings import settings
from bllose_agent.services.team_manager import get_self_agent

router = APIRouter(prefix="/agent", tags=["agent"])


@router.get("/info", response_model=AgentInfoResponse)
async def get_agent_info():
    return AgentInfoResponse(
        name="BlloseAgent",
        version="0.1.0",
        model=settings.llm_model,
    )


@router.get("/status", response_model=list[AgentStatusResponse])
async def list_agent_statuses():
    """Return live status for all registered sub-agents."""
    sa = get_self_agent()
    return [
        AgentStatusResponse(
            name=s.name,
            role=s.role,
            status=s.status,
            details=s.details,
        )
        for s in sa.list_agent_statuses()
    ]


@router.get("/status/{name}", response_model=AgentStatusResponse)
async def get_agent_status(name: str):
    """Return live status for a single sub-agent."""
    sa = get_self_agent()
    s = sa.get_agent_status(name)
    return AgentStatusResponse(
        name=s.name,
        role=s.role,
        status=s.status,
        details=s.details,
    )


@router.get("/tokens", response_model=GlobalTokenStatsResponse)
async def get_token_stats():
    """Return token usage statistics for all agents."""
    sa = get_self_agent()
    tt = sa.token_tracker
    return GlobalTokenStatsResponse(
        agents=[
            TokenStatsResponse(
                agent_name=s.agent_name,
                total_input=s.total_input,
                total_output=s.total_output,
                total_tokens=s.total_tokens,
                max_input=s.max_input,
                turn_count=s.turn_count,
            )
            for s in tt.all_stats
        ],
        total_input=tt.total_input,
        total_output=tt.total_output,
        total_tokens=tt.total_tokens,
        max_input=tt.max_input,
        agent_count=tt.agent_count,
    )


@router.get("/history/{name}", response_model=AgentHistoryResponse)
async def get_agent_history(name: str):
    """Return full conversation-turn history for a single agent."""
    sa = get_self_agent()
    tracker = sa.token_tracker.agent(name)
    s = tracker.stats
    return AgentHistoryResponse(
        agent_name=s.agent_name,
        total_input=s.total_input,
        total_output=s.total_output,
        total_tokens=s.total_tokens,
        max_input=s.max_input,
        turn_count=s.turn_count,
        turns=[TurnRecord(**t) for t in tracker.turns],
    )
