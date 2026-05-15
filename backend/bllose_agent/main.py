import re
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from bllose_agent.agent.self_agent import SelfAgent
from bllose_agent.api.router import api_router
from bllose_agent.config.settings import settings
from bllose_agent.services.team_manager import set_self_agent


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: SelfAgent starts first, then spawns all sub-agents
    self_agent = SelfAgent()
    set_self_agent(self_agent)
    result = self_agent.start()
    print(f"[SelfAgent] Startup complete:\n{result}")

    """
    `@asynccontextmanager` 装饰器会重写函数的行为。  
    装饰器在底层把它等价转换成类似这样的结构：  

    ``` python
    class LifespanContext:
    async def __aenter__(self):
        self._gen = self._generator()
        await self._gen.__anext__()   # 执行到 yield，然后停住
        # 此时 self_agent.start() 已执行完毕

    async def __aexit__(self, *args):
        await self._gen.__anext__()   # 从 yield 恢复，执行 self_agent.stop()
    ```  

    uvicorn 收到关闭信号时（Ctrl+C、kill、SIGTERM），
    会调用 lifespan 上下文的 __aexit__，
    生成器从 yield 处恢复，执行后面的 stop()。
    """
    yield

    # Shutdown: stop all sub-agents gracefully
    result = self_agent.stop()
    print(f"[SelfAgent] Shutdown complete:\n{result}")


app = FastAPI(
    title="BlloseAgent",
    description="BlloseAgent Backend API — FastAPI + LangChain + LangGraph",
    version="0.1.0",
    lifespan=lifespan,
)

if settings.debug:
    app.add_middleware(
        CORSMiddleware,
        allow_origin_regex=r"https?://(localhost|127\.0\.0\.1)(:\d+)?",
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
else:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

app.include_router(api_router)
