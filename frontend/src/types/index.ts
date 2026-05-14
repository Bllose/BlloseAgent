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
