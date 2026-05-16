export interface AgentInfo {
  name: string;
  version: string;
  model: string;
  workplace: string;
}

export interface User {
  email: string;
  password: string;
}

export interface ChatMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
  thinking: string;
  timestamp: number;
}

export interface StreamEvent {
  type: "token" | "tool_start" | "tool_end" | "error";
  content?: string;
  name?: string;
  output?: string;
}

export interface AgentStatus {
  name: string;
  role: string;
  status: string;
  details: string;
}

export interface TokenStats {
  agent_name: string;
  total_input: number;
  total_output: number;
  total_tokens: number;
  max_input: number;
  turn_count: number;
  all_input: number;
  all_output: number;
}

export interface GlobalTokenStats {
  agents: TokenStats[];
  total_input: number;
  total_output: number;
  total_tokens: number;
  max_input: number;
  agent_count: number;
  total_all_input: number;
  total_all_output: number;
}

export interface GraphMessage {
  type: string;
  content?: string;
  content_blocks?: Record<string, unknown>[];
  name?: string;
  tool_call_id?: string;
  tool_calls?: { name: string; args: Record<string, unknown>; id: string }[];
  usage_metadata?: Record<string, unknown>;
}

export interface TurnRecord {
  input_estimated: number;
  output_actual: number;
  all_input: number;
  all_output: number;
  input_text: string;
  output_text: string;
  graph_messages: GraphMessage[];
  timestamp: number;
}

export interface AgentHistory {
  agent_name: string;
  total_input: number;
  total_output: number;
  total_tokens: number;
  max_input: number;
  turn_count: number;
  turns: TurnRecord[];
}
