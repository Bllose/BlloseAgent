"use client";

import { createContext, useCallback, useContext, useRef, useState } from "react";
import { postChatStream } from "@/lib/api";
import type { ChatMessage } from "@/types";

interface ChatContextValue {
  messages: ChatMessage[];
  isStreaming: boolean;
  sendMessage: (content: string) => void;
}

const ChatContext = createContext<ChatContextValue | null>(null);

export function ChatProvider({ children }: { children: React.ReactNode }) {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [isStreaming, setIsStreaming] = useState(false);
  const idCounter = useRef(0);

  const nextId = () => `${Date.now()}-${++idCounter.current}`;

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
    <ChatContext.Provider value={{ messages, isStreaming, sendMessage }}>
      {children}
    </ChatContext.Provider>
  );
}

export function useChatContext() {
  const ctx = useContext(ChatContext);
  if (!ctx) throw new Error("useChatContext must be used within ChatProvider");
  return ctx;
}
