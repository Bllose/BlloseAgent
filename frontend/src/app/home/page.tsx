"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/hooks/useAuth";
import { ChatPanel } from "@/components/chat/ChatPanel";
import { StatusPanel } from "@/components/status/StatusPanel";
import { getTokenStats } from "@/lib/api";

type Tab = "chat" | "status";

const TABS: { key: Tab; label: string }[] = [
  { key: "chat", label: "Chat" },
  { key: "status", label: "Status" },
];

export default function HomePage() {
  const { isLoggedIn, email, logout } = useAuth();
  const router = useRouter();
  const [activeTab, setActiveTab] = useState<Tab>("chat");
  const [totalTokens, setTotalTokens] = useState<number | null>(null);

  useEffect(() => {
    if (!isLoggedIn) {
      router.replace("/login");
    }
  }, [isLoggedIn, router]);

  useEffect(() => {
    let cancelled = false;
    async function fetchTokens() {
      try {
        const stats = await getTokenStats();
        if (!cancelled) setTotalTokens(stats.total_tokens);
      } catch {
        // token stats not critical — ignore errors
      }
    }
    fetchTokens();
    const interval = setInterval(fetchTokens, 8000);
    return () => { cancelled = true; clearInterval(interval); };
  }, []);

  if (!isLoggedIn) return null;

  return (
    <div style={{ minHeight: "100vh", background: "#f0f2f5", display: "flex", flexDirection: "column" }}>
      {/* Top bar */}
      <header
        style={{
          background: "#fff",
          padding: "0 24px",
          height: 56,
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          boxShadow: "0 1px 4px rgba(0,0,0,0.06)",
          flexShrink: 0,
        }}
      >
        <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
          <span style={{ fontSize: 18, fontWeight: 700 }}>BlloseAgent</span>
          {totalTokens !== null && totalTokens > 0 && (
            <span
              style={{
                fontSize: 11,
                color: "#888",
                background: "#f5f5f5",
                padding: "2px 10px",
                borderRadius: 10,
              }}
            >
              {totalTokens >= 1000
                ? `${(totalTokens / 1000).toFixed(1)}K`
                : totalTokens}{" "}
              tokens
            </span>
          )}
        </div>

        <div style={{ display: "flex", alignItems: "center", gap: 16 }}>
          <span style={{ fontSize: 14, color: "#666" }}>{email}</span>
          <button
            onClick={logout}
            style={{
              padding: "6px 16px",
              border: "1px solid #d9d9d9",
              borderRadius: 6,
              background: "#fff",
              fontSize: 13,
              cursor: "pointer",
            }}
          >
            Logout
          </button>
        </div>
      </header>

      {/* Tab bar */}
      <nav
        style={{
          background: "#fff",
          borderBottom: "1px solid #f0f0f0",
          display: "flex",
          gap: 0,
          padding: "0 24px",
          flexShrink: 0,
        }}
      >
        {TABS.map((tab) => (
          <button
            key={tab.key}
            onClick={() => setActiveTab(tab.key)}
            style={{
              padding: "12px 20px",
              border: "none",
              background: "none",
              fontSize: 14,
              fontWeight: activeTab === tab.key ? 600 : 400,
              color: activeTab === tab.key ? "#1677ff" : "#666",
              borderBottom: activeTab === tab.key ? "2px solid #1677ff" : "2px solid transparent",
              cursor: "pointer",
              transition: "color 0.2s, border-color 0.2s",
            }}
          >
            {tab.label}
          </button>
        ))}
      </nav>

      {/* Tab content */}
      <main
        style={{
          flex: 1,
          minHeight: 0,
          display: "flex",
          flexDirection: "column",
          overflow: "hidden",
        }}
      >
        <div
          style={{
            flex: 1,
            minHeight: 0,
            display: "flex",
            flexDirection: "column",
            background: "#fff",
            overflow: "hidden",
          }}
        >
          <div style={{ display: activeTab === "chat" ? "flex" : "none", flex: 1, minHeight: 0, flexDirection: "column" }}>
            <ChatPanel />
          </div>
          <div style={{ display: activeTab === "status" ? "flex" : "none", flex: 1, minHeight: 0, flexDirection: "column" }}>
            <StatusPanel />
          </div>
        </div>
      </main>
    </div>
  );
}
