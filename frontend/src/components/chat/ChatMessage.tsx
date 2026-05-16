"use client";

import type { ChatMessage as ChatMessageType } from "@/types";

export function ChatMessage({ message }: { message: ChatMessageType }) {
  const isUser = message.role === "user";

  return (
    <div
      style={{
        display: "flex",
        justifyContent: isUser ? "flex-end" : "flex-start",
        marginBottom: 20,
        paddingLeft: isUser ? 48 : 0,
        paddingRight: isUser ? 0 : 48,
      }}
    >
      <div style={{ maxWidth: "100%" }}>
        {/* Thinking section */}
        {message.thinking && (
          <div
            style={{
              padding: "10px 16px",
              marginBottom: 8,
              borderRadius: "var(--radius)",
              background: "var(--color-primary-bg)",
              border: "1px solid #ede9fe",
              color: "var(--color-text-secondary)",
              fontSize: 12,
              lineHeight: 1.6,
              whiteSpace: "pre-wrap",
              wordBreak: "break-word",
            }}
          >
            <div
              style={{
                fontSize: 10,
                fontWeight: 600,
                textTransform: "uppercase",
                letterSpacing: "0.08em",
                color: "var(--color-primary)",
                marginBottom: 6,
              }}
            >
              Thinking
            </div>
            {message.thinking}
          </div>
        )}

        {/* Content bubble */}
        {message.content && (
          <div
            style={{
              padding: "12px 18px",
              borderRadius: "var(--radius-lg)",
              background: isUser ? "var(--color-primary)" : "var(--color-bg)",
              color: isUser ? "#fff" : "var(--color-text)",
              border: isUser ? "none" : "1px solid var(--color-border)",
              whiteSpace: "pre-wrap",
              wordBreak: "break-word",
              lineHeight: 1.65,
              fontSize: 14,
            }}
          >
            {message.content}
          </div>
        )}

        {/* Loading dots */}
        {!message.thinking && !message.content && (
          <div
            style={{
              padding: "14px 20px",
              borderRadius: "var(--radius-lg)",
              background: "var(--color-bg)",
              border: "1px solid var(--color-border)",
              display: "flex",
              alignItems: "center",
              gap: 6,
            }}
          >
            <span style={{ fontSize: 11, color: "var(--color-text-muted)" }}>
              Thinking
            </span>
            <span style={{ display: "flex", gap: 3 }}>
              <Dot delay={0} />
              <Dot delay={0.15} />
              <Dot delay={0.3} />
            </span>
          </div>
        )}
      </div>
    </div>
  );
}

function Dot({ delay }: { delay: number }) {
  return (
    <span
      style={{
        width: 5,
        height: 5,
        borderRadius: "50%",
        background: "var(--color-primary)",
        opacity: 0.4,
        animation: `pulse 1s ${delay}s ease-in-out infinite`,
      }}
    />
  );
}
