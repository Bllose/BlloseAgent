from pydantic import BaseModel


class AgentInfoResponse(BaseModel):
    name: str
    version: str
    model: str
