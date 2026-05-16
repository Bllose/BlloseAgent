from pydantic import BaseModel


class AgentInfoResponse(BaseModel):
    name: str
    version: str
    model: str
    workplace: str = ""


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
    all_input: int = 0
    all_output: int = 0


class GlobalTokenStatsResponse(BaseModel):
    agents: list[TokenStatsResponse]
    total_input: int
    total_output: int
    total_tokens: int
    max_input: int
    agent_count: int
    total_all_input: int = 0
    total_all_output: int = 0


class TurnRecord(BaseModel):
    input_estimated: int
    output_actual: int
    all_input: int = 0
    all_output: int = 0
    input_text: str
    output_text: str
    graph_messages: list[dict] = []
    timestamp: float


class AgentHistoryResponse(BaseModel):
    agent_name: str
    total_input: int
    total_output: int
    total_tokens: int
    max_input: int
    turn_count: int
    turns: list[TurnRecord]
