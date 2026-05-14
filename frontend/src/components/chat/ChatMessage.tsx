"use client";

import type { ChatMessage as ChatMessageType } from "@/types";

export function ChatMessage({ message }: { message: ChatMessageType }) {
  const isUser = message.role === "user";

  return (
    <div
      style={{
        display: "flex",
        justifyContent: isUser ? "flex-end" : "flex-start",
        marginBottom: 16,
      }}
    >
      <div style={{ maxWidth: "75%" }}>
        {/* thinking 区域 — 灰色背板、小字体 */}
        {message.thinking && (
          <div
            style={{
              padding: "8px 14px",
              marginBottom: 6,
              borderRadius: 12,
              background: "#f5f5f5",
              color: "#999",
              fontSize: 12,
              lineHeight: 1.5,
              whiteSpace: "pre-wrap",
              wordBreak: "break-word",
              borderLeft: "3px solid #d9d9d9",
            }}
          >
            {message.thinking}
          </div>
        )}

        {/* content 区域 — 保持原有样式 */}
        {message.content && (
          <div
            style={{
              padding: "12px 18px",
              borderRadius: 16,
              background: isUser ? "#1677ff" : "#ffffff",
              color: isUser ? "#fff" : "#1a1a1a",
              boxShadow: "0 1px 3px rgba(0,0,0,0.08)",
              whiteSpace: "pre-wrap",
              wordBreak: "break-word",
              lineHeight: 1.6,
            }}
          >
            {message.content}
          </div>
        )}

        {/* 空消息时显示 loading */}
        {!message.thinking && !message.content && (
          <div
            style={{
              padding: "12px 18px",
              borderRadius: 16,
              background: "#ffffff",
              boxShadow: "0 1px 3px rgba(0,0,0,0.08)",
            }}
          >
            <span style={{ opacity: 0.4 }}>Thinking...</span>
          </div>
        )}
      </div>
    </div>
  );
}
