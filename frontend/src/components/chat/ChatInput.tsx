"use client";

import { useState, useCallback, type FormEvent } from "react";

interface ChatInputProps {
  onSend: (message: string) => void;
  disabled?: boolean;
}

export function ChatInput({ onSend, disabled }: ChatInputProps) {
  const [value, setValue] = useState("");

  const handleSubmit = useCallback(
    (e: FormEvent) => {
      e.preventDefault();
      const trimmed = value.trim();
      if (!trimmed || disabled) return;
      onSend(trimmed);
      setValue("");
    },
    [value, disabled, onSend],
  );

  const handleKeyDown = useCallback(
    (e: React.KeyboardEvent) => {
      if (e.key === "Enter" && !e.shiftKey) {
        e.preventDefault();
        handleSubmit(e);
      }
    },
    [handleSubmit],
  );

  return (
    <form
      onSubmit={handleSubmit}
      style={{
        display: "flex",
        gap: 10,
        padding: "16px 0 0",
        borderTop: "1px solid #f0f0f0",
      }}
    >
      <textarea
        value={value}
        onChange={(e) => setValue(e.target.value)}
        onKeyDown={handleKeyDown}
        placeholder="Type a message... (Enter to send, Shift+Enter for new line)"
        disabled={disabled}
        rows={2}
        style={{
          flex: 1,
          padding: "10px 14px",
          borderRadius: 10,
          border: "1px solid #e0e0e0",
          fontSize: 14,
          resize: "none",
          outline: "none",
          fontFamily: "inherit",
        }}
      />
      <button
        type="submit"
        disabled={disabled || !value.trim()}
        style={{
          padding: "10px 24px",
          borderRadius: 10,
          border: "none",
          background: disabled || !value.trim() ? "#d9d9d9" : "#1677ff",
          color: "#fff",
          fontSize: 14,
          fontWeight: 600,
          cursor: disabled || !value.trim() ? "not-allowed" : "pointer",
          alignSelf: "flex-end",
          whiteSpace: "nowrap",
        }}
      >
        Send
      </button>
    </form>
  );
}
