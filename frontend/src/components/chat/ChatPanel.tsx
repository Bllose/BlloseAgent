"use client";

import { useEffect, useRef } from "react";
import { useChatContext } from "@/context/ChatContext";
import { ChatMessage as MessageBubble } from "./ChatMessage";
import { ChatInput } from "./ChatInput";

export function ChatPanel() {
  const { messages, isStreaming, sendMessage } = useChatContext();
  const scrollRef = useRef<HTMLDivElement>(null);

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
