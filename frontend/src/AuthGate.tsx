import { useEffect, useState } from "react";

import App from "./App";
import { clearSession, fetchCurrentPrincipal, getAccessToken, getStoredPrincipal, type AuthPrincipal } from "./api/client";
import LoginPage from "./pages/LoginPage";

export default function AuthGate() {
  const [principal, setPrincipal] = useState<AuthPrincipal | null>(() => getStoredPrincipal());
  const [checking, setChecking] = useState(Boolean(getAccessToken()));

  useEffect(() => {
    if (!getAccessToken()) {
      setChecking(false);
      setPrincipal(null);
      return;
    }
    void fetchCurrentPrincipal()
      .then((verified) => setPrincipal(verified))
      .catch(() => {
        clearSession();
        setPrincipal(null);
      })
      .finally(() => setChecking(false));
  }, []);

  if (checking) {
    return <div style={{ minHeight: "100vh", display: "grid", placeItems: "center", background: "#f6f8fa", fontWeight: 700 }}>Verifying BattleReef session…</div>;
  }

  if (!principal) {
    return <LoginPage onAuthenticated={setPrincipal} />;
  }

  return (
    <>
      <App />
      <div style={{ position: "fixed", right: 18, bottom: 18, zIndex: 1000, background: "#fff", border: "1px solid #d0d7de", borderRadius: 10, padding: "8px 10px", boxShadow: "0 4px 16px rgba(140,149,159,.25)", fontSize: ".8rem" }}>
        <span style={{ fontWeight: 800 }}>{principal.username}</span>
        <span style={{ color: "#57606a" }}> · {principal.role}</span>
        <button
          type="button"
          onClick={() => { clearSession(); setPrincipal(null); }}
          style={{ marginLeft: 10, border: "1px solid #d0d7de", borderRadius: 6, background: "#f6f8fa", padding: "4px 7px", cursor: "pointer" }}
        >
          Sign out
        </button>
      </div>
    </>
  );
}
