"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { getAgentHistory } from "@/lib/api";
import type { AgentHistory, GraphMessage } from "@/types";

function formatTokens(n: number): string {
  if (n >= 1_000_000) return `${(n / 1_000_000).toFixed(1)}M`;
  if (n >= 1_000) return `${(n / 1_000).toFixed(1)}K`;
  return String(n);
}

function timeAgo(ts: number): string {
  const sec = Math.max(0, (Date.now() / 1000) - ts);
  if (sec < 60) return "just now";
  if (sec < 3600) return `${Math.floor(sec / 60)}m ago`;
  if (sec < 86400) return `${Math.floor(sec / 3600)}h ago`;
  return `${Math.floor(sec / 86400)}d ago`;
}

const MSG_TYPE_COLORS: Record<string, string> = {
  human: "#3b82f6",
  ai: "#8b5cf6",
  tool: "#22c55e",
  system: "#f59e0b",
};

export default function AgentDetailPage() {
  const params = useParams();
  const router = useRouter();
  const name = decodeURIComponent(String(params.name));

  const [history, setHistory] = useState<AgentHistory | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [expandedTurn, setExpandedTurn] = useState<number | null>(null);

  useEffect(() => {
    let cancelled = false;
    async function fetch() {
      try {
        const data = await getAgentHistory(name);
        if (!cancelled) {
          setHistory(data);
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
    fetch();
    return () => { cancelled = true; };
  }, [name]);

  return (
    <div
      style={{
        minHeight: "100vh",
        background: "var(--color-bg)",
      }}
    >
      {/* ── Top bar ────────────────────────────── */}
      <header
        style={{
          background: "var(--color-surface)",
          padding: "0 32px",
          height: 60,
          display: "flex",
          alignItems: "center",
          gap: 16,
          borderBottom: "1px solid var(--color-border-light)",
        }}
      >
        <button
          onClick={() => router.push("/home?tab=status")}
          style={{
            padding: "6px 14px",
            border: "1px solid var(--color-border)",
            borderRadius: "var(--radius-sm)",
            background: "var(--color-surface)",
            fontSize: 13,
            fontWeight: 500,
            color: "var(--color-text-secondary)",
            cursor: "pointer",
            fontFamily: "inherit",
          }}
        >
          &larr; Back
        </button>
        <div
          style={{
            width: 30,
            height: 30,
            borderRadius: "var(--radius-sm)",
            background: "linear-gradient(135deg, #4f46e5, #7c3aed)",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
          }}
        >
          <span style={{ color: "#fff", fontSize: 14, fontWeight: 700 }}>
            {name.charAt(0).toUpperCase()}
          </span>
        </div>
        <span style={{ fontSize: 16, fontWeight: 600, color: "var(--color-text)" }}>
          {name}
        </span>
      </header>

      {/* ── Body ───────────────────────────────── */}
      <main style={{ maxWidth: 900, margin: "0 auto", padding: "24px 32px" }}>
        {loading && (
          <div style={{ textAlign: "center", color: "var(--color-text-muted)", padding: 64, fontSize: 14 }}>
            Loading history...
          </div>
        )}

        {error && (
          <div style={{ textAlign: "center", color: "var(--color-error)", padding: 64, fontSize: 14 }}>
            Failed to load: {error}
          </div>
        )}

        {history && (
          <>
            {/* Stats summary card */}
            <div
              style={{
                background: "var(--color-surface)",
                borderRadius: "var(--radius-lg)",
                padding: "20px 28px",
                border: "1px solid var(--color-border-light)",
                marginBottom: 24,
                display: "flex",
                gap: 0,
                overflow: "hidden",
              }}
            >
              <StatCell label="Total Tokens" value={formatTokens(history.total_tokens)} />
              <StatCell label="Input" value={formatTokens(history.total_input)} borderLeft />
              <StatCell label="Output" value={formatTokens(history.total_output)} borderLeft />
              <StatCell label="Max Input" value={formatTokens(history.max_input)} borderLeft />
              <StatCell label="Turns" value={String(history.turn_count)} borderLeft />
            </div>

            {/* Turn list */}
            {history.turns.length === 0 ? (
              <div
                style={{
                  textAlign: "center",
                  color: "var(--color-text-muted)",
                  padding: 48,
                  fontSize: 14,
                  background: "var(--color-surface)",
                  borderRadius: "var(--radius-lg)",
                  border: "1px solid var(--color-border-light)",
                }}
              >
                No conversation turns recorded yet.
              </div>
            ) : (
              <div style={{ display: "flex", flexDirection: "column", gap: 16 }}>
                <h3
                  style={{
                    fontSize: 14,
                    fontWeight: 600,
                    color: "var(--color-text-secondary)",
                    marginBottom: 0,
                  }}
                >
                  Conversation History
                </h3>
                {history.turns.map((turn, i) => {
                  const expanded = expandedTurn === i;
                  return (
                    <div
                      key={i}
                      style={{
                        background: "var(--color-surface)",
                        borderRadius: "var(--radius)",
                        padding: "20px 24px",
                        border: "1px solid var(--color-border-light)",
                      }}
                    >
                      {/* Turn header */}
                      <div
                        style={{
                          display: "flex",
                          alignItems: "center",
                          justifyContent: "space-between",
                          marginBottom: 14,
                          flexWrap: "wrap",
                          gap: 8,
                        }}
                      >
                        <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
                          <span
                            style={{
                              fontSize: 12,
                              fontWeight: 600,
                              color: "var(--color-primary)",
                              background: "var(--color-primary-bg)",
                              padding: "3px 12px",
                              borderRadius: 100,
                            }}
                          >
                            Turn {i + 1}
                          </span>
                          {turn.graph_messages.length > 0 && (
                            <button
                              onClick={() =>
                                setExpandedTurn(expanded ? null : i)
                              }
                              style={{
                                fontSize: 11,
                                fontWeight: 600,
                                color: expanded
                                  ? "var(--color-primary-hover)"
                                  : "var(--color-text-secondary)",
                                background: expanded
                                  ? "var(--color-primary-bg)"
                                  : "var(--color-bg)",
                                border: "1px solid var(--color-border)",
                                borderRadius: "var(--radius-sm)",
                                padding: "3px 12px",
                                cursor: "pointer",
                                fontFamily: "inherit",
                                transition: "all var(--transition)",
                              }}
                            >
                              {expanded
                                ? "Hide Trace"
                                : `Trace (${turn.graph_messages.length} msgs)`}
                            </button>
                          )}
                        </div>
                        <div style={{ display: "flex", gap: 14, fontSize: 12, color: "var(--color-text-muted)" }}>
                          <span title="Estimated input tokens">
                            In: {formatTokens(turn.input_estimated)}
                          </span>
                          <span title="Actual output tokens">
                            Out: {formatTokens(turn.output_actual)}
                          </span>
                          <span>{timeAgo(turn.timestamp)}</span>
                        </div>
                      </div>

                      {/* Input */}
                      <div style={{ marginBottom: 12 }}>
                        <div
                          style={{
                            fontSize: 11,
                            fontWeight: 600,
                            textTransform: "uppercase",
                            letterSpacing: "0.06em",
                            color: "var(--color-text-muted)",
                            marginBottom: 6,
                          }}
                        >
                          Input
                        </div>
                        <div
                          style={{
                            padding: "10px 14px",
                            background: "var(--color-bg)",
                            borderRadius: "var(--radius-sm)",
                            border: "1px solid var(--color-border-light)",
                            fontSize: 13,
                            lineHeight: 1.6,
                            whiteSpace: "pre-wrap",
                            wordBreak: "break-word",
                            color: "var(--color-text)",
                            maxHeight: 200,
                            overflowY: "auto",
                          }}
                        >
                          {turn.input_text || "(empty)"}
                        </div>
                      </div>

                      {/* Output */}
                      <div style={{ marginBottom: expanded ? 14 : 0 }}>
                        <div
                          style={{
                            fontSize: 11,
                            fontWeight: 600,
                            textTransform: "uppercase",
                            letterSpacing: "0.06em",
                            color: "var(--color-text-muted)",
                            marginBottom: 6,
                          }}
                        >
                          Output
                        </div>
                        <div
                          style={{
                            padding: "10px 14px",
                            background: "var(--color-primary-bg)",
                            borderRadius: "var(--radius-sm)",
                            border: "1px solid #ede9fe",
                            fontSize: 13,
                            lineHeight: 1.6,
                            whiteSpace: "pre-wrap",
                            wordBreak: "break-word",
                            color: "var(--color-text)",
                            maxHeight: 300,
                            overflowY: "auto",
                          }}
                        >
                          {turn.output_text || "(empty)"}
                        </div>
                      </div>

                      {/* Graph trace (expandable) */}
                      {expanded && (
                        <div
                          style={{
                            borderTop: "1px solid var(--color-border-light)",
                            paddingTop: 14,
                          }}
                        >
                          <div
                            style={{
                              fontSize: 11,
                              fontWeight: 600,
                              textTransform: "uppercase",
                              letterSpacing: "0.06em",
                              color: "var(--color-text-muted)",
                              marginBottom: 10,
                            }}
                          >
                            Graph Messages ({turn.graph_messages.length})
                          </div>
                          <div
                            style={{
                              display: "flex",
                              flexDirection: "column",
                              gap: 8,
                            }}
                          >
                            {turn.graph_messages.map((msg, mi) => (
                              <GraphMessageRow key={mi} msg={msg} index={mi} />
                            ))}
                          </div>
                        </div>
                      )}
                    </div>
                  );
                })}
              </div>
            )}
          </>
        )}
      </main>
    </div>
  );
}

function GraphMessageRow({
  msg,
  index,
}: {
  msg: GraphMessage;
  index: number;
}) {
  const typeColor = MSG_TYPE_COLORS[msg.type] || "#9ca3af";
  const content =
    msg.content ||
    (msg.content_blocks
      ? JSON.stringify(msg.content_blocks, null, 2)
      : "");

  return (
    <div
      style={{
        background: "var(--color-bg)",
        borderRadius: "var(--radius-sm)",
        border: "1px solid var(--color-border-light)",
        overflow: "hidden",
      }}
    >
      {/* Row header */}
      <div
        style={{
          display: "flex",
          alignItems: "center",
          gap: 10,
          padding: "8px 14px",
          borderBottom: "1px solid var(--color-border-light)",
        }}
      >
        <span
          style={{
            fontSize: 10,
            fontWeight: 700,
            color: typeColor,
            background: `${typeColor}18`,
            padding: "2px 8px",
            borderRadius: 4,
            textTransform: "uppercase",
          }}
        >
          {msg.type}
        </span>
        <span
          style={{
            fontSize: 11,
            fontWeight: 500,
            color: "var(--color-text-secondary)",
          }}
        >
          #{index + 1}
        </span>
        {msg.name && (
          <span
            style={{
              fontSize: 10,
              color: "var(--color-text-muted)",
              fontFamily: "var(--font-mono)",
            }}
          >
            {msg.name}
          </span>
        )}
        {msg.usage_metadata && (
          <span style={{ fontSize: 10, color: "var(--color-text-muted)", marginLeft: "auto" }}>
            Tokens:{" "}
            {String(msg.usage_metadata.input_tokens ?? "?")}/
            {String(msg.usage_metadata.output_tokens ?? "?")}
          </span>
        )}
      </div>

      {/* Tool calls (AI messages) */}
      {msg.tool_calls && msg.tool_calls.length > 0 && (
        <div
          style={{
            padding: "8px 14px",
            borderBottom: "1px solid var(--color-border-light)",
            background: "#fafafe",
          }}
        >
          <div
            style={{
              fontSize: 10,
              fontWeight: 600,
              color: "var(--color-text-muted)",
              marginBottom: 6,
            }}
          >
            TOOL CALLS
          </div>
          {msg.tool_calls.map((tc, tci) => (
            <div
              key={tci}
              style={{
                fontSize: 12,
                fontFamily: "var(--font-mono)",
                color: "var(--color-text-secondary)",
                marginBottom: 4,
              }}
            >
              <span style={{ fontWeight: 600, color: "var(--color-primary)" }}>
                {tc.name}
              </span>
              ({JSON.stringify(tc.args)})
            </div>
          ))}
        </div>
      )}

      {/* Content */}
      {content && (
        <div
          style={{
            padding: "10px 14px",
            fontSize: 12,
            lineHeight: 1.6,
            whiteSpace: "pre-wrap",
            wordBreak: "break-word",
            color: "var(--color-text)",
            fontFamily:
              msg.type === "tool" ? "var(--font-mono)" : "inherit",
            maxHeight: 300,
            overflowY: "auto",
          }}
        >
          {content}
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
        padding: "8px 16px",
        textAlign: "center",
        borderLeft: borderLeft ? "1px solid var(--color-border-light)" : "none",
      }}
    >
      <div style={{ fontSize: 11, color: "var(--color-text-muted)", marginBottom: 4, fontWeight: 500 }}>
        {label}
      </div>
      <div style={{ fontSize: 18, fontWeight: 700, color: "var(--color-text)" }}>
        {value}
      </div>
    </div>
  );
}
