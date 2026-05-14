"use client";

import { useState } from "react";
import Link from "next/link";
import { validateUser } from "@/lib/auth";
import { useAuth } from "@/hooks/useAuth";

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
      {error && (
        <p style={{ color: "#ff4d4f", marginBottom: 16, fontSize: 14 }}>{error}</p>
      )}

      <div style={{ marginBottom: 16 }}>
        <label style={{ display: "block", marginBottom: 6, fontSize: 14, fontWeight: 500 }}>
          Email
        </label>
        <input
          type="email"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          placeholder="Enter your email"
          style={{
            width: "100%",
            padding: "10px 12px",
            border: "1px solid #d9d9d9",
            borderRadius: 8,
            fontSize: 14,
            outline: "none",
          }}
        />
      </div>

      <div style={{ marginBottom: 24 }}>
        <label style={{ display: "block", marginBottom: 6, fontSize: 14, fontWeight: 500 }}>
          Password
        </label>
        <input
          type="password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          placeholder="Enter your password"
          style={{
            width: "100%",
            padding: "10px 12px",
            border: "1px solid #d9d9d9",
            borderRadius: 8,
            fontSize: 14,
            outline: "none",
          }}
        />
      </div>

      <button
        type="submit"
        style={{
          width: "100%",
          padding: "10px 0",
          background: "#1677ff",
          color: "#fff",
          border: "none",
          borderRadius: 8,
          fontSize: 16,
          fontWeight: 600,
          cursor: "pointer",
        }}
      >
        Log In
      </button>

      <p style={{ textAlign: "center", marginTop: 16, fontSize: 14, color: "#666" }}>
        Don&apos;t have an account?{" "}
        <Link href="/register" style={{ color: "#1677ff", textDecoration: "none" }}>
          Register
        </Link>
      </p>
    </form>
  );
}
