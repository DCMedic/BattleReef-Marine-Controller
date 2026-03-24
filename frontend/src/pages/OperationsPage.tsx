import { useEffect, useMemo, useState } from "react";

import { fetchRecentCommands, fetchSystemSummary } from "../api/queries";
import { DeviceStateTile } from "../components/DeviceStateTile";
import { RecentCommandsTable } from "../components/RecentCommandsTable";
import { useBattleReefEventStream } from "../hooks/useBattleReefEventStream";
import type { CommandListResponse, SystemSummaryResponse } from "../types";

export default function OperationsPage() {
  const [summary, setSummary] = useState<SystemSummaryResponse | null>(null);
  const [commands, setCommands] = useState<CommandListResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const { snapshot, connected, error: streamError } = useBattleReefEventStream();

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

  const liveSummary = snapshot?.summary ?? null;
  const liveCommands = snapshot?.commands ?? [];
  const liveDeviceStates = snapshot?.device_states ?? [];
  const lastUpdated = useMemo(() => {
    if (!snapshot?.timestamp) {
      return null;
    }

    return new Date(snapshot.timestamp).toLocaleString();
  }, [snapshot]);

  const displayedSummary = liveSummary ?? summary;
  const displayedCommands = liveCommands.length > 0 ? liveCommands : commands?.items ?? [];

  return (
    <div style={{ padding: "24px" }}>
      <div style={{ maxWidth: "1400px", margin: "0 auto" }}>
        <div style={{ marginBottom: "24px" }}>
          <h1 style={{ margin: 0, fontSize: "2rem", fontWeight: 800 }}>
            Operations
          </h1>
          <p style={{ marginTop: "8px", color: "#57606a", fontSize: "1rem" }}>
            Command lifecycle visibility, recent activity, current device state auditing, and live stream monitoring.
          </p>
        </div>

        <div style={{ marginBottom: "24px" }}>
          <LiveStreamStatusCard
            connected={connected}
            lastUpdated={lastUpdated}
            error={streamError}
          />
        </div>

        {loading && !displayedSummary ? (
          <div style={{ color: "#57606a" }}>Loading operations data...</div>
        ) : null}

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

        {displayedSummary ? (
          <>
            <div
              style={{
                display: "grid",
                gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))",
                gap: "16px",
                marginBottom: "24px",
              }}
            >
              <SummaryCard
                label="Total Commands"
                value={displayedSummary.counts.commands_total}
                tone="default"
              />
              <SummaryCard
                label="Queued"
                value={displayedSummary.counts.commands_queued}
                tone={displayedSummary.counts.commands_queued > 0 ? "warning" : "success"}
              />
              <SummaryCard
                label="Dispatched"
                value={displayedSummary.counts.commands_dispatched}
                tone="default"
              />
              <SummaryCard
                label="Completed"
                value={displayedSummary.counts.commands_completed}
                tone="success"
              />
              <SummaryCard
                label="Failed"
                value={displayedSummary.counts.commands_failed}
                tone={displayedSummary.counts.commands_failed > 0 ? "danger" : "success"}
              />
            </div>

            <div style={{ marginBottom: "24px" }}>
              <RecentCommandsTable items={displayedCommands} />
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
              {liveDeviceStates.length === 0 && displayedSummary.device_states.length === 0 ? (
                <div style={{ color: "#57606a" }}>No device states available.</div>
              ) : liveDeviceStates.length > 0 ? (
                liveDeviceStates.map((item) => (
                  <DeviceStateTile
                    key={item.device_key}
                    item={{
                      device_key: item.device_key,
                      state_payload: item.state_payload,
                      state_source: item.state_source,
                      updated_at: item.updated_at,
                    }}
                  />
                ))
              ) : (
                displayedSummary.device_states.map((item) => (
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

function LiveStreamStatusCard({
  connected,
  lastUpdated,
  error,
}: {
  connected: boolean;
  lastUpdated: string | null;
  error: string | null;
}) {
  const tone = !connected
    ? { bg: "#ffebe9", border: "#ff818266", fg: "#cf222e" }
    : error
    ? { bg: "#fff8c5", border: "#d4a72c66", fg: "#9a6700" }
    : { bg: "#dafbe1", border: "#4ac26b66", fg: "#1a7f37" };

  return (
    <section
      style={{
        background: tone.bg,
        border: `1px solid ${tone.border}`,
        borderRadius: "12px",
        padding: "16px",
      }}
    >
      <div style={{ fontWeight: 800, color: tone.fg, marginBottom: "10px" }}>
        Live Stream Status
      </div>

      <div
        style={{
          display: "grid",
          gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))",
          gap: "12px",
        }}
      >
        <div>
          <div style={{ fontSize: "0.8rem", color: tone.fg, fontWeight: 700, marginBottom: "4px" }}>
            Connection
          </div>
          <div style={{ fontSize: "0.95rem", fontWeight: 800, color: tone.fg }}>
            {connected ? "Connected" : "Disconnected"}
          </div>
        </div>

        <div>
          <div style={{ fontSize: "0.8rem", color: tone.fg, fontWeight: 700, marginBottom: "4px" }}>
            Last Update
          </div>
          <div style={{ fontSize: "0.95rem", fontWeight: 800, color: tone.fg }}>
            {lastUpdated ?? "No live update received yet"}
          </div>
        </div>

        <div>
          <div style={{ fontSize: "0.8rem", color: tone.fg, fontWeight: 700, marginBottom: "4px" }}>
            Stream Error
          </div>
          <div style={{ fontSize: "0.95rem", fontWeight: 800, color: tone.fg }}>
            {error ?? "None"}
          </div>
        </div>
      </div>
    </section>
  );
}

function SummaryCard({
  label,
  value,
  tone,
}: {
  label: string;
  value: number;
  tone: "default" | "warning" | "danger" | "success";
}) {
  const palette =
    tone === "danger"
      ? { bg: "#ffebe9", fg: "#cf222e", border: "#ff818266" }
      : tone === "warning"
      ? { bg: "#fff8c5", fg: "#9a6700", border: "#d4a72c66" }
      : tone === "success"
      ? { bg: "#dafbe1", fg: "#1a7f37", border: "#4ac26b66" }
      : { bg: "#ffffff", fg: "#1f2328", border: "#d0d7de" };

  return (
    <div
      style={{
        border: `1px solid ${palette.border}`,
        borderRadius: "12px",
        padding: "16px",
        background: palette.bg,
        boxShadow: "0 1px 3px rgba(0,0,0,0.06)",
      }}
    >
      <div
        style={{
          fontSize: "0.85rem",
          fontWeight: 700,
          color: tone === "default" ? "#57606a" : palette.fg,
          marginBottom: "8px",
        }}
      >
        {label}
      </div>
      <div
        style={{
          fontSize: "1.8rem",
          fontWeight: 800,
          color: palette.fg,
        }}
      >
        {value.toLocaleString()}
      </div>
    </div>
  );
}