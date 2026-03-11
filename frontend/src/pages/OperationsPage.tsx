import { useEffect, useState } from "react";

import { fetchRecentCommands, fetchSystemSummary } from "../api/queries";
import { DeviceStateTile } from "../components/DeviceStateTile";
import { RecentCommandsTable } from "../components/RecentCommandsTable";
import type { CommandListResponse, SystemSummaryResponse } from "../types";

export default function OperationsPage() {
  const [summary, setSummary] = useState<SystemSummaryResponse | null>(null);
  const [commands, setCommands] = useState<CommandListResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  async function loadData() {
    try {
      const [summaryData, commandData] = await Promise.all([
        fetchSystemSummary(),
        fetchRecentCommands(),
      ]);

      setSummary(summaryData);
      setCommands(commandData);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load operations page.");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    void loadData();
    const interval = window.setInterval(loadData, 5000);
    return () => window.clearInterval(interval);
  }, []);

  return (
    <div style={{ padding: "24px" }}>
      <div style={{ maxWidth: "1400px", margin: "0 auto" }}>
        <div style={{ marginBottom: "24px" }}>
          <h1 style={{ margin: 0, fontSize: "2rem", fontWeight: 800 }}>
            Operations
          </h1>
          <p style={{ marginTop: "8px", color: "#57606a", fontSize: "1rem" }}>
            Command lifecycle visibility, recent activity, and current device state auditing.
          </p>
        </div>

        {loading && !summary ? <div style={{ color: "#57606a" }}>Loading operations data...</div> : null}

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
          <>
            <div
              style={{
                display: "grid",
                gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))",
                gap: "16px",
                marginBottom: "24px",
              }}
            >
              <SummaryCard label="Total Commands" value={summary.counts.commands_total} />
              <SummaryCard label="Queued" value={summary.counts.commands_queued} />
              <SummaryCard label="Dispatched" value={summary.counts.commands_dispatched} />
              <SummaryCard label="Completed" value={summary.counts.commands_completed} />
              <SummaryCard label="Failed" value={summary.counts.commands_failed} />
            </div>

            <div style={{ marginBottom: "24px" }}>
              <RecentCommandsTable items={commands?.items ?? []} />
            </div>

            <div style={{ marginBottom: "12px" }}>
              <h2 style={{ margin: 0, fontSize: "1.25rem", fontWeight: 700 }}>
                Device States
              </h2>
            </div>

            <div
              style={{
                display: "grid",
                gridTemplateColumns: "repeat(auto-fit, minmax(280px, 1fr))",
                gap: "16px",
              }}
            >
              {summary.device_states.length === 0 ? (
                <div style={{ color: "#57606a" }}>No device states available.</div>
              ) : (
                summary.device_states.map((item) => (
                  <DeviceStateTile key={item.device_key} item={item} />
                ))
              )}
            </div>
          </>
        ) : null}
      </div>
    </div>
  );
}

function SummaryCard({
  label,
  value,
}: {
  label: string;
  value: number;
}) {
  return (
    <div
      style={{
        border: "1px solid #d0d7de",
        borderRadius: "12px",
        padding: "16px",
        background: "#ffffff",
        boxShadow: "0 1px 3px rgba(0,0,0,0.06)",
      }}
    >
      <div
        style={{
          fontSize: "0.85rem",
          fontWeight: 700,
          color: "#57606a",
          marginBottom: "8px",
        }}
      >
        {label}
      </div>
      <div
        style={{
          fontSize: "1.8rem",
          fontWeight: 800,
          color: "#1f2328",
        }}
      >
        {value.toLocaleString()}
      </div>
    </div>
  );
}