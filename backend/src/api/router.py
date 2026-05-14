from fastapi import APIRouter

from src.api.health import router as health_router
from src.api.chat import router as chat_router
from src.api.agent import router as agent_router
from src.api.intent import router as intent_router

api_router = APIRouter(prefix="/api")
api_router.include_router(health_router)
api_router.include_router(chat_router)
api_router.include_router(agent_router)
api_router.include_router(intent_router)
