import { FormEvent, useEffect, useState } from "react";

import { apiGet, apiPost, apiPut } from "../api/client";

type PrincipalRecord = {
  id: number;
  username: string;
  role: string;
  principal_type: string;
  active: boolean;
};

type CreatePrincipal = {
  username: string;
  password: string;
  role: string;
  principal_type: string;
};

export default function SecurityPanel({ onClose }: { onClose: () => void }) {
  const [items, setItems] = useState<PrincipalRecord[]>([]);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const [form, setForm] = useState<CreatePrincipal>({ username: "", password: "", role: "viewer", principal_type: "user" });

  async function load() {
    try {
      setItems(await apiGet<PrincipalRecord[]>("/auth/users"));
      setError("");
    } catch (exc) {
      setError(exc instanceof Error ? exc.message : "Failed to load principals.");
    }
  }

  useEffect(() => { void load(); }, []);

  async function create(event: FormEvent) {
    event.preventDefault();
    setBusy(true);
    try {
      await apiPost<PrincipalRecord, CreatePrincipal>("/auth/users", form);
      setForm({ username: "", password: "", role: "viewer", principal_type: "user" });
      await load();
    } catch (exc) {
      setError(exc instanceof Error ? exc.message : "Failed to create principal.");
    } finally {
      setBusy(false);
    }
  }

  async function update(username: string, changes: { role?: string; active?: boolean }) {
    setBusy(true);
    try {
      await apiPut<PrincipalRecord, typeof changes>(`/auth/users/${encodeURIComponent(username)}`, changes);
      await load();
    } catch (exc) {
      setError(exc instanceof Error ? exc.message : "Failed to update principal.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div style={{ position: "fixed", inset: 0, zIndex: 2000, background: "rgba(31,35,40,.45)", display: "grid", placeItems: "center", padding: 24 }}>
      <section style={{ width: "min(920px, 100%)", maxHeight: "90vh", overflow: "auto", background: "#fff", borderRadius: 14, border: "1px solid #d0d7de", boxShadow: "0 18px 50px rgba(31,35,40,.28)" }}>
        <header style={{ display: "flex", justifyContent: "space-between", gap: 16, alignItems: "center", padding: "20px 22px", borderBottom: "1px solid #d8dee4" }}>
          <div><div style={{ fontSize: "1.2rem", fontWeight: 800 }}>Security & Principals</div><div style={{ color: "#57606a", marginTop: 4, fontSize: ".86rem" }}>Administrator-only RBAC account and service-principal management.</div></div>
          <button type="button" onClick={onClose} style={{ border: "1px solid #d0d7de", background: "#f6f8fa", borderRadius: 8, padding: "7px 10px", cursor: "pointer" }}>Close</button>
        </header>

        <div style={{ padding: 22 }}>
          {error ? <div style={{ padding: 10, background: "#ffebe9", border: "1px solid #ff8182", color: "#cf222e", borderRadius: 8, marginBottom: 16 }}>{error}</div> : null}

          <form onSubmit={create} style={{ display: "grid", gridTemplateColumns: "1.1fr 1.4fr .9fr .9fr auto", gap: 10, alignItems: "end", marginBottom: 24 }}>
            <label style={{ display: "grid", gap: 5, fontSize: ".8rem", fontWeight: 700 }}>Username<input required minLength={3} value={form.username} onChange={(e) => setForm({ ...form, username: e.target.value })} style={{ padding: 9, border: "1px solid #d0d7de", borderRadius: 7 }} /></label>
            <label style={{ display: "grid", gap: 5, fontSize: ".8rem", fontWeight: 700 }}>Initial password<input required minLength={12} type="password" value={form.password} onChange={(e) => setForm({ ...form, password: e.target.value })} style={{ padding: 9, border: "1px solid #d0d7de", borderRadius: 7 }} /></label>
            <label style={{ display: "grid", gap: 5, fontSize: ".8rem", fontWeight: 700 }}>Role<select value={form.role} onChange={(e) => setForm({ ...form, role: e.target.value })} style={{ padding: 9, border: "1px solid #d0d7de", borderRadius: 7 }}><option>viewer</option><option>operator</option><option>engineer</option><option>administrator</option></select></label>
            <label style={{ display: "grid", gap: 5, fontSize: ".8rem", fontWeight: 700 }}>Type<select value={form.principal_type} onChange={(e) => setForm({ ...form, principal_type: e.target.value })} style={{ padding: 9, border: "1px solid #d0d7de", borderRadius: 7 }}><option value="user">user</option><option value="service">service</option></select></label>
            <button type="submit" disabled={busy} style={{ padding: "10px 13px", border: 0, borderRadius: 8, background: "#0969da", color: "#fff", fontWeight: 800, cursor: "pointer" }}>Create</button>
          </form>

          <div style={{ display: "grid", gap: 9 }}>
            {items.map((item) => (
              <div key={item.id} style={{ display: "grid", gridTemplateColumns: "1.5fr .8fr .8fr .7fr auto", alignItems: "center", gap: 10, border: "1px solid #d8dee4", borderRadius: 9, padding: "10px 12px" }}>
                <div><div style={{ fontWeight: 800 }}>{item.username}</div><div style={{ fontSize: ".75rem", color: "#57606a" }}>{item.principal_type}</div></div>
                <select value={item.role} disabled={busy} onChange={(e) => void update(item.username, { role: e.target.value })} style={{ padding: 7, border: "1px solid #d0d7de", borderRadius: 7 }}><option>viewer</option><option>operator</option><option>engineer</option><option>administrator</option></select>
                <span style={{ fontWeight: 700, color: item.active ? "#1a7f37" : "#cf222e" }}>{item.active ? "Active" : "Disabled"}</span>
                <span style={{ color: "#57606a", fontSize: ".82rem" }}>#{item.id}</span>
                <button type="button" disabled={busy} onClick={() => void update(item.username, { active: !item.active })} style={{ padding: "7px 10px", border: "1px solid #d0d7de", borderRadius: 7, background: item.active ? "#ffebe9" : "#dafbe1", cursor: "pointer" }}>{item.active ? "Disable" : "Enable"}</button>
              </div>
            ))}
          </div>
        </div>
      </section>
    </div>
  );
}
