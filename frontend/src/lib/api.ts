import type { AgentStatus, AgentHistory, AgentInfo, GlobalTokenStats } from "@/types";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

interface StreamCallbacks {
  onText: (token: string) => void;
  onThinking: (token: string) => void;
  onDone: () => void;
  onError: (err: Error) => void;
}

export async function postChatStream(
  message: string,
  callbacks: StreamCallbacks,
): Promise<void> {
  const { onText, onThinking, onDone, onError } = callbacks;

  try {
    const res = await fetch(`${API_URL}/api/chat/stream`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message }),
    });

    if (!res.ok || !res.body) {
      throw new Error(`HTTP ${res.status}`);
    }

    const reader = res.body.getReader();
    const decoder = new TextDecoder();
    let buffer = "";

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split("\n");
      buffer = lines.pop() || "";

      for (const line of lines) {
        if (!line.trim()) continue;
        if (!line.startsWith("data: ")) continue;

        const data = line.slice(6);
        if (data === "[DONE]") {
          onDone();
          return;
        }

        try {
          const parsed = JSON.parse(data);
          if (parsed.type === "text" && parsed.content) {
            onText(String(parsed.content));
          } else if (parsed.type === "thinking" && parsed.content) {
            onThinking(String(parsed.content));
          }
        } catch {
          // skip malformed JSON
        }
      }
    }

    onDone();
  } catch (err) {
    onError(err instanceof Error ? err : new Error(String(err)));
  }
}

export async function getAgentStatuses(): Promise<AgentStatus[]> {
  const res = await fetch(`${API_URL}/api/agent/status`);
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  return res.json();
}

export async function getAgentInfo(): Promise<AgentInfo> {
  const res = await fetch(`${API_URL}/api/agent/info`);
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  return res.json();
}

export async function getTokenStats(): Promise<GlobalTokenStats> {
  const res = await fetch(`${API_URL}/api/agent/tokens`);
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  return res.json();
}

export async function getAgentHistory(
  name: string,
): Promise<AgentHistory> {
  const res = await fetch(`${API_URL}/api/agent/history/${encodeURIComponent(name)}`);
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  return res.json();
}
