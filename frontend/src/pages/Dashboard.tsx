import { useEffect, useMemo, useState } from "react";

import { fetchSystemSummary } from "../api/queries";
import { DeviceStateTile } from "../components/DeviceStateTile";
import { MetricCard } from "../components/MetricCard";
import { SystemStatusPanel } from "../components/SystemStatusPanel";
import type { SensorLatestReading, SystemSummaryResponse } from "../types";

function formatReading(reading: SensorLatestReading | undefined): string {
  if (!reading) return "N/A";
  return `${reading.value} ${reading.unit}`;
}

function formatTimestamp(reading: SensorLatestReading | undefined): string {
  if (!reading) return "No reading available";
  return `Updated ${new Date(reading.reading_time).toLocaleTimeString()}`;
}

export default function Dashboard() {
  const [summary, setSummary] = useState<SystemSummaryResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  async function loadSummary() {
    try {
      const data = await fetchSystemSummary();
      setSummary(data);
      setError(null);
    } catch (err) {
      const message =
        err instanceof Error ? err.message : "Failed to load dashboard data.";
      setError(message);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadSummary();
    const interval = window.setInterval(loadSummary, 5000);
    return () => window.clearInterval(interval);
  }, []);

  const readingsByKey = useMemo(() => {
    const map = new Map<string, SensorLatestReading>();
    for (const reading of summary?.latest_readings ?? []) {
      map.set(reading.sensor_key, reading);
    }
    return map;
  }, [summary]);

  const temp = readingsByKey.get("tank_temp_main");
  const ph = readingsByKey.get("tank_ph_main");
  const salinity = readingsByKey.get("tank_salinity_main");
  const level = readingsByKey.get("sump_level_main");

  return (
    <div
      style={{
        padding: "24px",
        background: "#f6f8fa",
        minHeight: "100vh",
        color: "#1f2328",
      }}
    >
      <div style={{ maxWidth: "1400px", margin: "0 auto" }}>
        <div style={{ marginBottom: "24px" }}>
          <h1
            style={{
              margin: 0,
              fontSize: "2rem",
              fontWeight: 800,
            }}
          >
            BattleReef Operator Dashboard
          </h1>
          <p
            style={{
              marginTop: "8px",
              color: "#57606a",
              fontSize: "1rem",
            }}
          >
            Live telemetry, command lifecycle, and device state overview.
          </p>
        </div>

        {loading && !summary ? (
          <div style={{ color: "#57606a" }}>Loading dashboard data...</div>
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
              <MetricCard
                title="Temperature"
                value={formatReading(temp)}
                subtitle={formatTimestamp(temp)}
              />
              <MetricCard
                title="pH"
                value={formatReading(ph)}
                subtitle={formatTimestamp(ph)}
              />
              <MetricCard
                title="Salinity"
                value={formatReading(salinity)}
                subtitle={formatTimestamp(salinity)}
              />
              <MetricCard
                title="Sump Level"
                value={formatReading(level)}
                subtitle={formatTimestamp(level)}
              />
            </div>

            <div
              style={{
                display: "grid",
                gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))",
                gap: "16px",
                marginBottom: "24px",
              }}
            >
              <MetricCard
                title="Telemetry Records"
                value={summary.counts.telemetry_readings.toLocaleString()}
              />
              <MetricCard
                title="Commands Completed"
                value={summary.counts.commands_completed.toLocaleString()}
              />
              <MetricCard
                title="Commands Failed"
                value={summary.counts.commands_failed.toLocaleString()}
              />
              <MetricCard
                title="Tracked Devices"
                value={summary.counts.device_states.toLocaleString()}
              />
            </div>

            <div
              style={{
                display: "grid",
                gridTemplateColumns: "minmax(280px, 360px) 1fr",
                gap: "16px",
                alignItems: "start",
                marginBottom: "24px",
              }}
            >
              <SystemStatusPanel summary={summary} />

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
                    fontSize: "1rem",
                    fontWeight: 700,
                    color: "#1f2328",
                    marginBottom: "12px",
                  }}
                >
                  Command Summary
                </div>

                <div style={{ display: "grid", gap: "10px" }}>
                  <div style={{ display: "flex", justifyContent: "space-between" }}>
                    <span style={{ color: "#57606a", fontWeight: 600 }}>Total</span>
                    <span>{summary.counts.commands_total}</span>
                  </div>
                  <div style={{ display: "flex", justifyContent: "space-between" }}>
                    <span style={{ color: "#57606a", fontWeight: 600 }}>Queued</span>
                    <span>{summary.counts.commands_queued}</span>
                  </div>
                  <div style={{ display: "flex", justifyContent: "space-between" }}>
                    <span style={{ color: "#57606a", fontWeight: 600 }}>Dispatched</span>
                    <span>{summary.counts.commands_dispatched}</span>
                  </div>
                  <div style={{ display: "flex", justifyContent: "space-between" }}>
                    <span style={{ color: "#57606a", fontWeight: 600 }}>Completed</span>
                    <span>{summary.counts.commands_completed}</span>
                  </div>
                  <div style={{ display: "flex", justifyContent: "space-between" }}>
                    <span style={{ color: "#57606a", fontWeight: 600 }}>Failed</span>
                    <span>{summary.counts.commands_failed}</span>
                  </div>
                </div>
              </div>
            </div>

            <div style={{ marginBottom: "12px" }}>
              <h2
                style={{
                  margin: 0,
                  fontSize: "1.25rem",
                  fontWeight: 700,
                }}
              >
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