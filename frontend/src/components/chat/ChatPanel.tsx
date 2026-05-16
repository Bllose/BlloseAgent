"use client";

import { useEffect, useRef, useState } from "react";
import { useChatContext } from "@/context/ChatContext";
import { ChatMessage as MessageBubble } from "./ChatMessage";
import { ChatInput } from "./ChatInput";
import { getAgentInfo } from "@/lib/api";

export function ChatPanel() {
  const { messages, isStreaming, sendMessage } = useChatContext();
  const scrollRef = useRef<HTMLDivElement>(null);
  const [workplace, setWorkplace] = useState<string | null>(null);

  useEffect(() => {
    getAgentInfo().then(info => setWorkplace(info.workplace)).catch(() => {});
  }, []);

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages]);

  return (
    <div
      style={{
        display: "flex",
        flexDirection: "column",
        height: "100%",
        minHeight: 0,
      }}
    >
      <div
        ref={scrollRef}
        style={{
          flex: 1,
          minHeight: 0,
          overflowY: "auto",
          padding: "20px 20px 8px",
        }}
      >
        {messages.length === 0 && (
          <div
            style={{
              textAlign: "center",
              paddingTop: 80,
            }}
          >
            <div
              style={{
                width: 56,
                height: 56,
                borderRadius: "var(--radius)",
                background: "linear-gradient(135deg, #4f46e5, #7c3aed)",
                display: "inline-flex",
                alignItems: "center",
                justifyContent: "center",
                marginBottom: 18,
              }}
            >
              <span style={{ color: "#fff", fontSize: 26 }}>B</span>
            </div>
            <h2
              style={{
                fontSize: 18,
                fontWeight: 600,
                color: "var(--color-text)",
                marginBottom: 8,
              }}
            >
              Welcome to BlloseAgent
            </h2>
            <p style={{ fontSize: 13, color: "var(--color-text-muted)", lineHeight: 1.6 }}>
              Ask me to write code, read papers, or delegate tasks to the expert team.
              <br />
              Start a conversation below.
            </p>
            {workplace && (
              <div
                style={{
                  marginTop: 20,
                  display: "inline-flex",
                  alignItems: "center",
                  gap: 6,
                  padding: "6px 16px",
                  borderRadius: 100,
                  background: "var(--color-bg)",
                  border: "1px solid var(--color-border)",
                  fontSize: 12,
                  color: "var(--color-text-secondary)",
                  fontFamily: "var(--font-mono)",
                }}
              >
                <span style={{ fontSize: 11, fontWeight: 500, color: "var(--color-text-muted)" }}>
                  workspace
                </span>
                <span style={{ color: "var(--color-text)" }}>{workplace}</span>
              </div>
            )}
          </div>
        )}
        {messages.map((msg) => (
          <MessageBubble key={msg.id} message={msg} />
        ))}
      </div>

      <div style={{ flexShrink: 0 }}>
        <ChatInput onSend={sendMessage} disabled={isStreaming} />
      </div>
    </div>
  );
}
