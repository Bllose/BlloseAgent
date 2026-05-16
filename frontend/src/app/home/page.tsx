"use client";

import { Suspense, useEffect, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { useAuth } from "@/hooks/useAuth";
import { ChatPanel } from "@/components/chat/ChatPanel";
import { StatusPanel } from "@/components/status/StatusPanel";
import { getTokenStats } from "@/lib/api";

type Tab = "chat" | "status";

const TABS: { key: Tab; label: string; icon: string }[] = [
  { key: "chat", label: "Chat", icon: "💬" },
  { key: "status", label: "Agents", icon: "⚡" },
];

function formatTokens(n: number): string {
  if (n >= 1_000_000) return `${(n / 1_000_000).toFixed(1)}M`;
  if (n >= 1_000) return `${(n / 1_000).toFixed(1)}K`;
  return String(n);
}

function HomePageInner() {
  const { isLoggedIn, email, logout } = useAuth();
  const router = useRouter();
  const searchParams = useSearchParams();
  const [activeTab, setActiveTab] = useState<Tab>("chat");
  const [totalTokens, setTotalTokens] = useState<number | null>(null);

  // Sync tab from URL (handles back-navigation from agent detail)
  useEffect(() => {
    const t = searchParams.get("tab");
    if (t === "status") setActiveTab("status");
  }, [searchParams]);

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
        // token stats not critical
      }
    }
    fetchTokens();
    const interval = setInterval(fetchTokens, 8000);
    return () => {
      cancelled = true;
      clearInterval(interval);
    };
  }, []);

  if (!isLoggedIn) return null;

  return (
    <div
      style={{
        height: "100vh",
        display: "flex",
        flexDirection: "column",
        background: "var(--color-bg)",
        overflow: "hidden",
      }}
    >
      {/* ── Header ────────────────────────────────── */}
      <header
        style={{
          background: "var(--color-surface)",
          padding: "0 32px",
          height: 60,
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          borderBottom: "1px solid var(--color-border-light)",
          flexShrink: 0,
        }}
      >
        {/* Left — branding */}
        <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
          <div
            style={{
              width: 34,
              height: 34,
              borderRadius: "var(--radius-sm)",
              background: "linear-gradient(135deg, #4f46e5, #7c3aed)",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              flexShrink: 0,
            }}
          >
            <span style={{ color: "#fff", fontSize: 16, fontWeight: 700 }}>B</span>
          </div>
          <span
            style={{
              fontSize: 17,
              fontWeight: 700,
              color: "var(--color-text)",
              letterSpacing: "-0.01em",
            }}
          >
            BlloseAgent
          </span>
          {totalTokens !== null && totalTokens > 0 && (
            <span
              style={{
                fontSize: 11,
                fontWeight: 600,
                color: "var(--color-text-secondary)",
                background: "var(--color-bg)",
                padding: "3px 12px",
                borderRadius: 100,
                border: "1px solid var(--color-border)",
              }}
            >
              {formatTokens(totalTokens)} tokens
            </span>
          )}
        </div>

        {/* Right — user */}
        <div style={{ display: "flex", alignItems: "center", gap: 14 }}>
          <span
            style={{
              fontSize: 13,
              color: "var(--color-text-secondary)",
            }}
          >
            {email}
          </span>
          <button
            onClick={logout}
            style={{
              padding: "7px 18px",
              border: "1px solid var(--color-border)",
              borderRadius: "var(--radius-sm)",
              background: "var(--color-surface)",
              fontSize: 13,
              fontWeight: 500,
              color: "var(--color-text-secondary)",
              cursor: "pointer",
              fontFamily: "inherit",
              transition: "all var(--transition)",
            }}
            onMouseEnter={(e) => {
              e.currentTarget.style.borderColor = "var(--color-error)";
              e.currentTarget.style.color = "var(--color-error)";
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.borderColor = "var(--color-border)";
              e.currentTarget.style.color = "var(--color-text-secondary)";
            }}
          >
            Logout
          </button>
        </div>
      </header>

      {/* ── Tab bar ──────────────────────────────── */}
      <nav
        style={{
          background: "var(--color-surface)",
          borderBottom: "1px solid var(--color-border-light)",
          display: "flex",
          gap: 4,
          padding: "0 32px",
          flexShrink: 0,
        }}
      >
        {TABS.map((tab) => {
          const active = activeTab === tab.key;
          return (
            <button
              key={tab.key}
              onClick={() => setActiveTab(tab.key)}
              style={{
                padding: "12px 22px",
                border: "none",
                background: "none",
                fontSize: 14,
                fontWeight: active ? 600 : 400,
                color: active ? "var(--color-primary)" : "var(--color-text-secondary)",
                borderBottom: active
                  ? "2px solid var(--color-primary)"
                  : "2px solid transparent",
                cursor: "pointer",
                fontFamily: "inherit",
                transition: "all var(--transition)",
                display: "flex",
                alignItems: "center",
                gap: 7,
              }}
            >
              <span style={{ fontSize: 15 }}>{tab.icon}</span>
              {tab.label}
            </button>
          );
        })}
      </nav>

      {/* ── Content ──────────────────────────────── */}
      <main
        style={{
          flex: 1,
          minHeight: 0,
          display: "flex",
          flexDirection: "column",
          overflow: "hidden",
          padding: "24px 32px",
        }}
      >
        <div
          style={{
            flex: 1,
            minHeight: 0,
            display: "flex",
            flexDirection: "column",
            background: "var(--color-surface)",
            borderRadius: "var(--radius-lg)",
            boxShadow: "var(--shadow-xs)",
            border: "1px solid var(--color-border-light)",
            overflow: "hidden",
          }}
        >
          <div
            style={{
              display: activeTab === "chat" ? "flex" : "none",
              flex: 1,
              minHeight: 0,
              flexDirection: "column",
            }}
          >
            <ChatPanel />
          </div>
          <div
            style={{
              display: activeTab === "status" ? "flex" : "none",
              flex: 1,
              minHeight: 0,
              flexDirection: "column",
            }}
          >
            <StatusPanel />
          </div>
        </div>
      </main>
    </div>
  );
}

export default function HomePage() {
  return (
    <Suspense
      fallback={
        <div
          style={{
            height: "100vh",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            background: "var(--color-bg)",
            color: "var(--color-text-muted)",
            fontSize: 14,
          }}
        >
          Loading...
        </div>
      }
    >
      <HomePageInner />
    </Suspense>
  );
}
