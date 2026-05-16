from pydantic import BaseModel


class AgentInfoResponse(BaseModel):
    name: str
    version: str
    model: str


class AgentStatusResponse(BaseModel):
    name: str
    role: str
    status: str
    details: str = ""


class TokenStatsResponse(BaseModel):
    agent_name: str
    total_input: int
    total_output: int
    total_tokens: int
    max_input: int
    turn_count: int


class GlobalTokenStatsResponse(BaseModel):
    agents: list[TokenStatsResponse]
    total_input: int
    total_output: int
    total_tokens: int
    max_input: int
    agent_count: int


class TurnRecord(BaseModel):
    input_estimated: int
    output_actual: int
    input_text: str
    output_text: str
    timestamp: float


class AgentHistoryResponse(BaseModel):
    agent_name: str
    total_input: int
    total_output: int
    total_tokens: int
    max_input: int
    turn_count: int
    turns: list[TurnRecord]
