from fastapi import APIRouter

from bllose_agent.api.health import router as health_router
from bllose_agent.api.chat import router as chat_router
from bllose_agent.api.agent import router as agent_router
from bllose_agent.api.intent import router as intent_router

api_router = APIRouter(prefix="/api")
api_router.include_router(health_router)
api_router.include_router(chat_router)
api_router.include_router(agent_router)
api_router.include_router(intent_router)
