import { useEffect, useState } from "react";

import App from "./App";
import { AUTH_CLEARED_EVENT, clearSession, fetchCurrentPrincipal, getAccessToken, getStoredPrincipal, type AuthPrincipal } from "./api/client";
import SecurityPanel from "./components/SecurityPanel";
import LoginPage from "./pages/LoginPage";

export default function AuthGate() {
  const tokenAtLoad = getAccessToken();
  const [principal, setPrincipal] = useState<AuthPrincipal | null>(() => tokenAtLoad ? getStoredPrincipal() : null);
  const [checking, setChecking] = useState(Boolean(tokenAtLoad));
  const [showSecurity, setShowSecurity] = useState(false);

  useEffect(() => {
    const onCleared = () => {
      setPrincipal(null);
      setShowSecurity(false);
      setChecking(false);
    };
    window.addEventListener(AUTH_CLEARED_EVENT, onCleared);

    if (!getAccessToken()) {
      setChecking(false);
      setPrincipal(null);
    } else {
      void fetchCurrentPrincipal()
        .then((verified) => setPrincipal(verified))
        .catch(() => clearSession())
        .finally(() => setChecking(false));
    }

    return () => window.removeEventListener(AUTH_CLEARED_EVENT, onCleared);
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
      {showSecurity && principal.role === "administrator" ? <SecurityPanel onClose={() => setShowSecurity(false)} /> : null}
      <div style={{ position: "fixed", right: 18, bottom: 18, zIndex: 1000, background: "#fff", border: "1px solid #d0d7de", borderRadius: 10, padding: "8px 10px", boxShadow: "0 4px 16px rgba(140,149,159,.25)", fontSize: ".8rem" }}>
        <span style={{ fontWeight: 800 }}>{principal.username}</span>
        <span style={{ color: "#57606a" }}> · {principal.role} · {principal.principal_type}</span>
        {principal.role === "administrator" ? (
          <button type="button" onClick={() => setShowSecurity(true)} style={{ marginLeft: 10, border: "1px solid #0969da", borderRadius: 6, background: "#ddf4ff", color: "#0969da", padding: "4px 7px", cursor: "pointer", fontWeight: 700 }}>
            Security
          </button>
        ) : null}
        <button
          type="button"
          onClick={() => clearSession()}
          style={{ marginLeft: 10, border: "1px solid #d0d7de", borderRadius: 6, background: "#f6f8fa", padding: "4px 7px", cursor: "pointer" }}
        >
          Sign out
        </button>
      </div>
    </>
  );
}
