import { useEffect, useState } from "react";

import { fetchSystemSummary } from "../api/queries";
import { ManualControlPanel } from "../components/ManualControlPanel";
import type { CommandResponse, SystemSummaryResponse } from "../types";

export default function ManualControlPage() {
  const [summary, setSummary] = useState<SystemSummaryResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  async function loadData() {
    try {
      const summaryData = await fetchSystemSummary();
      setSummary(summaryData);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load manual control page.");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    void loadData();
    const interval = window.setInterval(loadData, 5000);
    return () => window.clearInterval(interval);
  }, []);

  function handleCommandSent(_command: CommandResponse) {
    window.setTimeout(() => {
      void loadData();
    }, 1000);
  }

  function handleDeviceModeChanged() {
    window.setTimeout(() => {
      void loadData();
    }, 500);
  }

  return (
    <div style={{ padding: "24px" }}>
      <div style={{ maxWidth: "1400px", margin: "0 auto" }}>
        <div style={{ marginBottom: "24px" }}>
          <h1 style={{ margin: 0, fontSize: "2rem", fontWeight: 800 }}>
            Manual Control
          </h1>
          <p style={{ marginTop: "8px", color: "#57606a", fontSize: "1rem" }}>
            Directly control aquarium devices and switch between automatic and manual operating modes.
          </p>
        </div>

        {loading && !summary ? <div style={{ color: "#57606a" }}>Loading manual controls...</div> : null}

        {error ? (
          <div
            style={{
              marginBottom: "20px",
              padding: "12px 16px",
              border: "1px solid #cf222e",
              borderRadius: "10px",
              background: "#ffebe9",
              color: "#cf222e",
            }}
          >
            {error}
          </div>
        ) : null}

        {summary ? (
          <ManualControlPanel
            deviceStates={summary.device_states}
            onCommandSent={handleCommandSent}
            onDeviceModeChanged={handleDeviceModeChanged}
          />
        ) : null}
      </div>
    </div>
  );
}