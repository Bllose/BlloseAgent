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

  const canSend = value.trim() && !disabled;

  return (
    <form
      onSubmit={handleSubmit}
      style={{
        display: "flex",
        gap: 10,
        padding: "16px 20px 20px",
        borderTop: "1px solid var(--color-border-light)",
        background: "var(--color-surface)",
      }}
    >
      <textarea
        value={value}
        onChange={(e) => setValue(e.target.value)}
        onKeyDown={handleKeyDown}
        placeholder="Type a message... (Enter ↵ to send)"
        disabled={disabled}
        rows={2}
        style={{
          flex: 1,
          padding: "11px 16px",
          borderRadius: "var(--radius)",
          border: "1px solid var(--color-border)",
          fontSize: 14,
          resize: "none",
          outline: "none",
          fontFamily: "inherit",
          background: "var(--color-bg)",
          transition: "border-color var(--transition)",
          lineHeight: 1.5,
        }}
      />
      <button
        type="submit"
        disabled={!canSend}
        style={{
          padding: "0 28px",
          borderRadius: "var(--radius)",
          border: "none",
          background: canSend ? "var(--color-primary)" : "var(--color-border)",
          color: "#fff",
          fontSize: 14,
          fontWeight: 600,
          cursor: canSend ? "pointer" : "default",
          fontFamily: "inherit",
          transition: "background var(--transition)",
          alignSelf: "flex-end",
          height: 42,
          whiteSpace: "nowrap",
        }}
      >
        Send
      </button>
    </form>
  );
}
