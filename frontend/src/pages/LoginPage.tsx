import { FormEvent, useState } from "react";

import { login, type AuthPrincipal } from "../api/client";

export default function LoginPage({ onAuthenticated }: { onAuthenticated: (principal: AuthPrincipal) => void }) {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  async function submit(event: FormEvent) {
    event.preventDefault();
    setBusy(true);
    setError("");
    try {
      const session = await login(username, password);
      onAuthenticated({ username: session.username, role: session.role });
    } catch {
      setError("Authentication failed. Verify your username and password.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div style={{ minHeight: "100vh", display: "grid", placeItems: "center", background: "#f6f8fa", padding: 24 }}>
      <form onSubmit={submit} style={{ width: "100%", maxWidth: 420, background: "#fff", border: "1px solid #d0d7de", borderRadius: 14, padding: 28, boxShadow: "0 8px 28px rgba(140,149,159,.2)" }}>
        <div style={{ fontSize: "1.45rem", fontWeight: 800, marginBottom: 6 }}>BattleReef</div>
        <div style={{ color: "#57606a", marginBottom: 24 }}>Authenticate to the Marine Controller operator console.</div>
        <label style={{ display: "grid", gap: 6, marginBottom: 16, fontWeight: 700 }}>
          Username
          <input value={username} onChange={(e) => setUsername(e.target.value)} autoComplete="username" required style={{ padding: 11, border: "1px solid #d0d7de", borderRadius: 8 }} />
        </label>
        <label style={{ display: "grid", gap: 6, marginBottom: 18, fontWeight: 700 }}>
          Password
          <input type="password" value={password} onChange={(e) => setPassword(e.target.value)} autoComplete="current-password" required style={{ padding: 11, border: "1px solid #d0d7de", borderRadius: 8 }} />
        </label>
        {error ? <div style={{ background: "#ffebe9", color: "#cf222e", border: "1px solid #ff8182", borderRadius: 8, padding: 10, marginBottom: 14 }}>{error}</div> : null}
        <button type="submit" disabled={busy} style={{ width: "100%", padding: 12, border: 0, borderRadius: 8, background: "#0969da", color: "#fff", fontWeight: 800, cursor: "pointer" }}>
          {busy ? "Authenticating…" : "Sign in"}
        </button>
      </form>
    </div>
  );
}
