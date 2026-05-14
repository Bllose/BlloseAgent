"use client";

import { useState } from "react";
import Link from "next/link";
import { registerUser } from "@/lib/auth";
import { useAuth } from "@/hooks/useAuth";

export function RegisterForm() {
  const { login } = useAuth();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirm, setConfirm] = useState("");
  const [error, setError] = useState("");

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setError("");

    if (!email.trim() || !password.trim() || !confirm.trim()) {
      setError("Please fill in all fields");
      return;
    }

    if (password !== confirm) {
      setError("Passwords do not match");
      return;
    }

    if (password.length < 6) {
      setError("Password must be at least 6 characters");
      return;
    }

    if (!registerUser(email, password)) {
      setError("Email already registered");
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

      <div style={{ marginBottom: 16 }}>
        <label style={{ display: "block", marginBottom: 6, fontSize: 14, fontWeight: 500 }}>
          Password
        </label>
        <input
          type="password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          placeholder="At least 6 characters"
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
          Confirm Password
        </label>
        <input
          type="password"
          value={confirm}
          onChange={(e) => setConfirm(e.target.value)}
          placeholder="Re-enter your password"
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
        Register
      </button>

      <p style={{ textAlign: "center", marginTop: 16, fontSize: 14, color: "#666" }}>
        Already have an account?{" "}
        <Link href="/login" style={{ color: "#1677ff", textDecoration: "none" }}>
          Log In
        </Link>
      </p>
    </form>
  );
}
