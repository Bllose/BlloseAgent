"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import type { AgentStatus, TokenStats } from "@/types";
import { getAgentStatuses, getTokenStats } from "@/lib/api";

const STATUS_CONFIG: Record<string, { color: string; bg: string }> = {
  idle: { color: "#22c55e", bg: "#f0fdf4" },
  working: { color: "#3b82f6", bg: "#eff6ff" },
  starting: { color: "#f59e0b", bg: "#fffbeb" },
  shutdown: { color: "#9ca3af", bg: "#f9fafb" },
  error: { color: "#ef4444", bg: "#fef2f2" },
};

const ROLE_LABELS: Record<string, string> = {
  intent_recognition: "Intent Recognition",
  coding_leader: "Coding Leader",
  paper_leader: "Paper Leader",
  self_agent: "Self Agent",
};

function statusConfig(status: string) {
  return STATUS_CONFIG[status] || STATUS_CONFIG.shutdown;
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
  const router = useRouter();
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
      <div
        style={{
          textAlign: "center",
          color: "var(--color-text-muted)",
          padding: 64,
          fontSize: 14,
        }}
      >
        Loading agent status...
      </div>
    );
  }

  if (error) {
    return (
      <div
        style={{
          textAlign: "center",
          color: "var(--color-error)",
          padding: 64,
          fontSize: 14,
        }}
      >
        Failed to load: {error}
      </div>
    );
  }

  return (
    <div style={{ padding: "20px 24px 0", overflowY: "auto", height: "100%" }}>
      {/* Header */}
      <div
        style={{
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          marginBottom: 20,
        }}
      >
        <h2
          style={{
            margin: 0,
            fontSize: 16,
            fontWeight: 600,
            color: "var(--color-text)",
          }}
        >
          Agent Cluster
        </h2>
        <span style={{ fontSize: 12, color: "var(--color-text-muted)" }}>
          {agents.length} agent{agents.length !== 1 ? "s" : ""} &middot;
          auto-refresh every 5s
        </span>
      </div>

      {/* Grid */}
      <div
        style={{
          display: "grid",
          gridTemplateColumns: "repeat(auto-fill, minmax(340px, 1fr))",
          gap: 16,
        }}
      >
        {agents.map((a) => {
          const sc = statusConfig(a.status);
          const tokens = tokenMap[a.name];

          return (
            <div
              key={a.name}
              onClick={() => router.push(`/agent/${encodeURIComponent(a.name)}`)}
              style={{
                background: "var(--color-surface)",
                borderRadius: "var(--radius)",
                padding: "20px 24px",
                border: "1px solid var(--color-border-light)",
                display: "flex",
                flexDirection: "column",
                gap: 12,
                cursor: "pointer",
                transition: "box-shadow var(--transition), border-color var(--transition)",
              }}
              onMouseEnter={(e) => {
                e.currentTarget.style.borderColor = "var(--color-primary)";
                e.currentTarget.style.boxShadow = "var(--shadow)";
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.borderColor = "var(--color-border-light)";
                e.currentTarget.style.boxShadow = "none";
              }}
            >
              {/* Name + status */}
              <div
                style={{
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "space-between",
                }}
              >
                <span
                  style={{ fontSize: 15, fontWeight: 600, color: "var(--color-text)" }}
                >
                  {a.name}
                </span>
                <span
                  style={{
                    display: "inline-flex",
                    alignItems: "center",
                    gap: 6,
                    fontSize: 11,
                    fontWeight: 600,
                    color: sc.color,
                    background: sc.bg,
                    padding: "4px 12px",
                    borderRadius: 100,
                  }}
                >
                  <span
                    style={{
                      width: 7,
                      height: 7,
                      borderRadius: "50%",
                      background: sc.color,
                    }}
                  />
                  {a.status}
                </span>
              </div>

              {/* Role */}
              <div style={{ fontSize: 13, color: "var(--color-text-muted)" }}>
                {roleLabel(a.role)}
              </div>

              {/* Token stats */}
              {tokens && tokens.turn_count > 0 ? (
                <div
                  style={{
                    display: "flex",
                    gap: 0,
                    borderRadius: "var(--radius-sm)",
                    overflow: "hidden",
                    border: "1px solid var(--color-border-light)",
                  }}
                >
                  <StatCell label="Tokens" value={formatTokens(tokens.total_tokens)} />
                  <StatCell
                    label="In / Out"
                    value={`${formatTokens(tokens.total_input)} / ${formatTokens(tokens.total_output)}`}
                    borderLeft
                  />
                  <StatCell
                    label="All"
                    value={formatTokens(tokens.all_input + tokens.all_output)}
                    borderLeft
                  />
                  <StatCell
                    label="Max In"
                    value={formatTokens(tokens.max_input)}
                    borderLeft
                  />
                </div>
              ) : (
                <div
                  style={{
                    fontSize: 12,
                    color: "var(--color-text-muted)",
                    padding: "8px 12px",
                    background: "var(--color-bg)",
                    borderRadius: "var(--radius-sm)",
                    textAlign: "center",
                  }}
                >
                  No token usage yet
                </div>
              )}

              {/* Details */}
              {a.details && (
                <div
                  style={{
                    fontSize: 12,
                    color: "var(--color-text-secondary)",
                    lineHeight: 1.5,
                    padding: "10px 14px",
                    background: "var(--color-bg)",
                    borderRadius: "var(--radius-sm)",
                    border: "1px solid var(--color-border-light)",
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
        <div
          style={{
            textAlign: "center",
            color: "var(--color-text-muted)",
            padding: 64,
            fontSize: 14,
          }}
        >
          No agents registered.
        </div>
      )}
    </div>
  );
}

function StatCell({
  label,
  value,
  borderLeft,
}: {
  label: string;
  value: string;
  borderLeft?: boolean;
}) {
  return (
    <div
      style={{
        flex: 1,
        padding: "8px 6px",
        background: "var(--color-bg)",
        textAlign: "center",
        borderLeft: borderLeft ? "1px solid var(--color-border-light)" : "none",
        minWidth: 0,
      }}
    >
      <div
        style={{
          fontSize: 10,
          color: "var(--color-text-muted)",
          marginBottom: 2,
          fontWeight: 500,
        }}
      >
        {label}
      </div>
      <div style={{
        fontSize: 12,
        fontWeight: 600,
        color: "var(--color-text)",
        whiteSpace: "nowrap",
        overflow: "hidden",
        textOverflow: "ellipsis",
      }}>
        {value}
      </div>
    </div>
  );
}
