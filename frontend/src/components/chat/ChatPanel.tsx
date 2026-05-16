"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { postChatStream } from "@/lib/api";
import type { ChatMessage } from "@/types";
import { ChatMessage as MessageBubble } from "./ChatMessage";
import { ChatInput } from "./ChatInput";

export function ChatPanel() {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [isStreaming, setIsStreaming] = useState(false);
  const idCounter = useRef(0);
  const scrollRef = useRef<HTMLDivElement>(null);

  const nextId = () => `${Date.now()}-${++idCounter.current}`;

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages]);

  const makeAssistant = (): ChatMessage => ({
    id: nextId(),
    role: "assistant",
    content: "",
    thinking: "",
    timestamp: Date.now(),
  });

  const updateLast = (
    updater: (msg: ChatMessage) => Partial<ChatMessage>,
  ) => {
    setMessages((prev) => {
      const updated = [...prev];
      const last = updated[updated.length - 1];
      if (last && last.role === "assistant") {
        updated[updated.length - 1] = { ...last, ...updater(last) };
      }
      return updated;
    });
  };

  const sendMessage = useCallback((content: string) => {
    const userMsg: ChatMessage = {
      id: nextId(),
      role: "user",
      content,
      thinking: "",
      timestamp: Date.now(),
    };

    setMessages((prev) => [...prev, userMsg, makeAssistant()]);
    setIsStreaming(true);

    postChatStream(content, {
      onText: (token) => {
        updateLast((m) => ({ content: m.content + token }));
      },
      onThinking: (token) => {
        updateLast((m) => ({ thinking: m.thinking + token }));
      },
      onDone: () => setIsStreaming(false),
      onError: (err) => {
        setIsStreaming(false);
        updateLast((m) => ({
          content: m.content || `Error: ${err.message}`,
        }));
      },
    });
  }, []);

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
