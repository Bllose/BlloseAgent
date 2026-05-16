import { LoginForm } from "@/components/auth/LoginForm";

export default function LoginPage() {
  return (
    <div
      style={{
        minHeight: "100vh",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        background: "linear-gradient(135deg, #f5f3ff 0%, #eef2ff 50%, #f8fafc 100%)",
      }}
    >
      <div
        style={{
          width: 420,
          padding: "44px 40px",
          background: "var(--color-surface)",
          borderRadius: "var(--radius-xl)",
          boxShadow: "var(--shadow-lg)",
          border: "1px solid var(--color-border-light)",
        }}
      >
        {/* Logo mark */}
        <div style={{ textAlign: "center", marginBottom: 28 }}>
          <div
            style={{
              width: 48,
              height: 48,
              borderRadius: "var(--radius)",
              background: "linear-gradient(135deg, #4f46e5, #7c3aed)",
              display: "inline-flex",
              alignItems: "center",
              justifyContent: "center",
              marginBottom: 16,
            }}
          >
            <span style={{ color: "#fff", fontSize: 22, fontWeight: 700 }}>B</span>
          </div>
          <h1
            style={{
              fontSize: 22,
              fontWeight: 700,
              color: "var(--color-text)",
              marginBottom: 4,
            }}
          >
            BlloseAgent
          </h1>
          <p style={{ fontSize: 13, color: "var(--color-text-muted)" }}>
            Sign in to your workspace
          </p>
        </div>

        <LoginForm />
      </div>
    </div>
  );
}
