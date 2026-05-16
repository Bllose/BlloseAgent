"use client";

import { useState } from "react";
import Link from "next/link";
import { validateUser } from "@/lib/auth";
import { useAuth } from "@/hooks/useAuth";

const s = {
  error: {
    padding: "10px 14px",
    marginBottom: 20,
    borderRadius: "var(--radius-sm)",
    background: "var(--color-error-bg)",
    color: "var(--color-error)",
    fontSize: 13,
    border: "1px solid #fecaca",
  },
  field: { marginBottom: 18 },
  label: {
    display: "block",
    marginBottom: 6,
    fontSize: 13,
    fontWeight: 600,
    color: "var(--color-text-secondary)",
    letterSpacing: "0.01em",
  },
  input: {
    width: "100%",
    padding: "11px 14px",
    border: "1px solid var(--color-border)",
    borderRadius: "var(--radius)",
    fontSize: 14,
    outline: "none",
    fontFamily: "inherit",
    background: "var(--color-bg)",
    transition: "border-color var(--transition), box-shadow var(--transition)",
    boxShadow: "0 1px 2px rgba(0,0,0,0.03)",
  },
  button: {
    width: "100%",
    padding: "12px 0",
    background: "var(--color-primary)",
    color: "#fff",
    border: "none",
    borderRadius: "var(--radius)",
    fontSize: 15,
    fontWeight: 600,
    cursor: "pointer",
    fontFamily: "inherit",
    transition: "background var(--transition), transform var(--transition)",
    marginTop: 4,
  },
  footer: {
    textAlign: "center" as const,
    marginTop: 20,
    fontSize: 13,
    color: "var(--color-text-secondary)",
  },
  link: { color: "var(--color-primary)", fontWeight: 600 },
};

export function LoginForm() {
  const { login } = useAuth();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setError("");

    if (!email.trim() || !password.trim()) {
      setError("Please fill in all fields");
      return;
    }

    if (!validateUser(email, password)) {
      setError("Invalid email or password");
      return;
    }

    login(email);
  };

  return (
    <form onSubmit={handleSubmit}>
      {error && <div style={s.error}>{error}</div>}

      <div style={s.field}>
        <label style={s.label}>Email</label>
        <input
          type="email"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          placeholder="Enter your email"
          style={s.input}
        />
      </div>

      <div style={s.field}>
        <label style={s.label}>Password</label>
        <input
          type="password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          placeholder="Enter your password"
          style={s.input}
        />
      </div>

      <button type="submit" style={s.button}>
        Log In
      </button>

      <p style={s.footer}>
        Don&apos;t have an account?{" "}
        <Link href="/register" style={s.link}>
          Register
        </Link>
      </p>
    </form>
  );
}
