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
}

export interface GlobalTokenStats {
  agents: TokenStats[];
  total_input: number;
  total_output: number;
  total_tokens: number;
  max_input: number;
  agent_count: number;
}
