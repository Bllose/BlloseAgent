"use client";

import { useEffect, useState } from "react";
import type { AgentStatus, TokenStats } from "@/types";
import { getAgentStatuses, getTokenStats } from "@/lib/api";

const STATUS_COLORS: Record<string, string> = {
  idle: "#22c55e",
  working: "#3b82f6",
  starting: "#f59e0b",
  shutdown: "#9ca3af",
  error: "#ef4444",
};

const ROLE_LABELS: Record<string, string> = {
  intent_recognition: "Intent Recognition",
  coding_leader: "Coding Leader",
  paper_leader: "Paper Leader",
  self_agent: "Self Agent",
};

function statusColor(status: string): string {
  return STATUS_COLORS[status] || "#9ca3af";
}

function roleLabel(role: string): string {
  return ROLE_LABELS[role] || role;
}

function formatTokens(n: number): string {
  if (n >= 1_000_000) return `${(n / 1_000_000).toFixed(1)}M`;
  if (n >= 1_000) return `${(n / 1_000).toFixed(1)}K`;
  return String(n);
}

export function StatusPanel() {
  const [agents, setAgents] = useState<AgentStatus[]>([]);
  const [tokenMap, setTokenMap] = useState<Record<string, TokenStats>>({});
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;

    async function fetchData() {
      try {
        const [statuses, tokenData] = await Promise.all([
          getAgentStatuses(),
          getTokenStats(),
        ]);
        if (!cancelled) {
          setAgents(statuses);
          const map: Record<string, TokenStats> = {};
          for (const t of tokenData.agents) {
            map[t.agent_name] = t;
          }
          setTokenMap(map);
          setError(null);
          setLoading(false);
        }
      } catch (err) {
        if (!cancelled) {
          setError(err instanceof Error ? err.message : "Failed to fetch");
          setLoading(false);
        }
      }
    }

    fetchData();
    const interval = setInterval(fetchData, 5000);
    return () => {
      cancelled = true;
      clearInterval(interval);
    };
  }, []);

  if (loading) {
    return (
      <div style={{ textAlign: "center", color: "#999", padding: 48, fontSize: 14 }}>
        Loading agent status...
      </div>
    );
  }

  if (error) {
    return (
      <div style={{ textAlign: "center", color: "#ef4444", padding: 48, fontSize: 14 }}>
        Failed to load: {error}
      </div>
    );
  }

  return (
    <div style={{ padding: "20px 24px", overflowY: "auto", height: "100%" }}>
      <div
        style={{
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          marginBottom: 20,
        }}
      >
        <h2 style={{ margin: 0, fontSize: 16, fontWeight: 600, color: "#333" }}>
          Agent Cluster
        </h2>
        <span style={{ fontSize: 12, color: "#999" }}>
          {agents.length} agent{agents.length !== 1 ? "s" : ""} &middot; auto-refresh every 5s
        </span>
      </div>

      <div
        style={{
          display: "grid",
          gridTemplateColumns: "repeat(auto-fill, minmax(280px, 1fr))",
          gap: 16,
        }}
      >
        {agents.map((a) => {
          const tokens = tokenMap[a.name];
          return (
            <div
              key={a.name}
              style={{
                background: "#fff",
                borderRadius: 10,
                padding: "20px 24px",
                border: "1px solid #e8e8e8",
                boxShadow: "0 1px 3px rgba(0,0,0,0.04)",
                display: "flex",
                flexDirection: "column",
                gap: 10,
              }}
            >
              {/* Header: name + status badge */}
              <div
                style={{
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "space-between",
                }}
              >
                <span style={{ fontSize: 15, fontWeight: 600, color: "#333" }}>
                  {a.name}
                </span>
                <span
                  style={{
                    display: "inline-flex",
                    alignItems: "center",
                    gap: 5,
                    fontSize: 11,
                    fontWeight: 500,
                    color: statusColor(a.status),
                    background: `${statusColor(a.status)}14`,
                    padding: "3px 10px",
                    borderRadius: 20,
                  }}
                >
                  <span
                    style={{
                      width: 7,
                      height: 7,
                      borderRadius: "50%",
                      background: statusColor(a.status),
                      display: "inline-block",
                    }}
                  />
                  {a.status}
                </span>
              </div>

              {/* Role */}
              <div style={{ fontSize: 13, color: "#888" }}>
                {roleLabel(a.role)}
              </div>

              {/* Token usage */}
              {tokens && tokens.turn_count > 0 ? (
                <div
                  style={{
                    display: "flex",
                    gap: 12,
                    padding: "10px 12px",
                    background: "#f8f9ff",
                    borderRadius: 8,
                    border: "1px solid #eef0ff",
                  }}
                >
                  <div style={{ flex: 1 }}>
                    <div style={{ fontSize: 10, color: "#aaa", marginBottom: 2 }}>
                      Tokens
                    </div>
                    <div style={{ fontSize: 14, fontWeight: 600, color: "#444" }}>
                      {formatTokens(tokens.total_tokens)}
                    </div>
                  </div>
                  <div style={{ flex: 1 }}>
                    <div style={{ fontSize: 10, color: "#aaa", marginBottom: 2 }}>
                      In / Out
                    </div>
                    <div style={{ fontSize: 12, color: "#666" }}>
                      {formatTokens(tokens.total_input)} / {formatTokens(tokens.total_output)}
                    </div>
                  </div>
                  <div style={{ flex: 1 }}>
                    <div style={{ fontSize: 10, color: "#aaa", marginBottom: 2 }}>
                      Max Input
                    </div>
                    <div style={{ fontSize: 12, color: "#666" }}>
                      {formatTokens(tokens.max_input)}
                    </div>
                  </div>
                </div>
              ) : (
                <div style={{ fontSize: 11, color: "#ccc" }}>
                  No token usage yet
                </div>
              )}

              {/* Details */}
              {a.details && (
                <div
                  style={{
                    fontSize: 12,
                    color: "#999",
                    lineHeight: 1.5,
                    padding: "8px 12px",
                    background: "#fafafa",
                    borderRadius: 6,
                  }}
                >
                  {a.details}
                </div>
              )}
            </div>
          );
        })}
      </div>

      {agents.length === 0 && (
        <div style={{ textAlign: "center", color: "#999", padding: 48, fontSize: 14 }}>
          No agents registered.
        </div>
      )}
    </div>
  );
}
