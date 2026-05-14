import { LoginForm } from "@/components/auth/LoginForm";

export default function LoginPage() {
  return (
    <div
      style={{
        minHeight: "100vh",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
      }}
    >
      <div
        style={{
          width: 400,
          padding: "40px 32px",
          background: "#fff",
          borderRadius: 12,
          boxShadow: "0 2px 12px rgba(0,0,0,0.08)",
        }}
      >
        <h1
          style={{
            fontSize: 24,
            fontWeight: 700,
            textAlign: "center",
            marginBottom: 8,
          }}
        >
          BlloseAgent
        </h1>
        <p
          style={{
            fontSize: 14,
            color: "#999",
            textAlign: "center",
            marginBottom: 32,
          }}
        >
          Log in to your account
        </p>
        <LoginForm />
      </div>
    </div>
  );
}
