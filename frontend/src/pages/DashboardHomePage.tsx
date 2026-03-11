import { useEffect, useMemo, useState } from "react";

import { fetchSystemSummary, fetchTelemetryHistory } from "../api/queries";
import { MetricCard } from "../components/MetricCard";
import { SystemStatusPanel } from "../components/SystemStatusPanel";
import { TelemetryMiniChart } from "../components/TelemetryMiniChart";
import type {
  SensorLatestReading,
  SystemSummaryResponse,
  TelemetryHistoryResponse,
  TelemetryHistorySeries,
} from "../types";

function formatReading(reading: SensorLatestReading | undefined): string {
  if (!reading) return "N/A";
  return `${reading.value} ${reading.unit}`;
}

function formatTimestamp(reading: SensorLatestReading | undefined): string {
  if (!reading) return "No reading available";
  return `Updated ${new Date(reading.reading_time).toLocaleTimeString()}`;
}

export default function DashboardHomePage() {
  const [summary, setSummary] = useState<SystemSummaryResponse | null>(null);
  const [history, setHistory] = useState<TelemetryHistoryResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  async function loadData() {
    try {
      const [summaryData, historyData] = await Promise.all([
        fetchSystemSummary(),
        fetchTelemetryHistory(),
      ]);
      setSummary(summaryData);
      setHistory(historyData);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load dashboard.");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    void loadData();
    const interval = window.setInterval(loadData, 5000);
    return () => window.clearInterval(interval);
  }, []);

  const readingsByKey = useMemo(() => {
    const map = new Map<string, SensorLatestReading>();
    for (const reading of summary?.latest_readings ?? []) {
      map.set(reading.sensor_key, reading);
    }
    return map;
  }, [summary]);

  const historyByKey = useMemo(() => {
    const map = new Map<string, TelemetryHistorySeries>();
    for (const series of history?.series ?? []) {
      map.set(series.sensor_key, series);
    }
    return map;
  }, [history]);

  const temp = readingsByKey.get("tank_temp_main");
  const ph = readingsByKey.get("tank_ph_main");
  const salinity = readingsByKey.get("tank_salinity_main");
  const level = readingsByKey.get("sump_level_main");

  return (
    <div style={{ padding: "24px" }}>
      <div style={{ maxWidth: "1400px", margin: "0 auto" }}>
        <div style={{ marginBottom: "24px" }}>
          <h1 style={{ margin: 0, fontSize: "2rem", fontWeight: 800 }}>
            Main Dashboard
          </h1>
          <p style={{ marginTop: "8px", color: "#57606a", fontSize: "1rem" }}>
            Live system overview, environmental telemetry, platform health, and trend visibility.
          </p>
        </div>

        {loading && !summary ? <div style={{ color: "#57606a" }}>Loading dashboard data...</div> : null}

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
              <MetricCard title="Temperature" value={formatReading(temp)} subtitle={formatTimestamp(temp)} />
              <MetricCard title="pH" value={formatReading(ph)} subtitle={formatTimestamp(ph)} />
              <MetricCard title="Salinity" value={formatReading(salinity)} subtitle={formatTimestamp(salinity)} />
              <MetricCard title="Sump Level" value={formatReading(level)} subtitle={formatTimestamp(level)} />
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
                  Overview Metrics
                </div>

                <div style={{ display: "grid", gap: "10px" }}>
                  <div style={{ display: "flex", justifyContent: "space-between" }}>
                    <span style={{ color: "#57606a", fontWeight: 600 }}>Telemetry Records</span>
                    <span>{summary.counts.telemetry_readings.toLocaleString()}</span>
                  </div>
                  <div style={{ display: "flex", justifyContent: "space-between" }}>
                    <span style={{ color: "#57606a", fontWeight: 600 }}>Commands Completed</span>
                    <span>{summary.counts.commands_completed.toLocaleString()}</span>
                  </div>
                  <div style={{ display: "flex", justifyContent: "space-between" }}>
                    <span style={{ color: "#57606a", fontWeight: 600 }}>Commands Failed</span>
                    <span>{summary.counts.commands_failed.toLocaleString()}</span>
                  </div>
                  <div style={{ display: "flex", justifyContent: "space-between" }}>
                    <span style={{ color: "#57606a", fontWeight: 600 }}>Tracked Devices</span>
                    <span>{summary.counts.device_states.toLocaleString()}</span>
                  </div>
                </div>
              </div>
            </div>

            <div
              style={{
                display: "grid",
                gridTemplateColumns: "repeat(auto-fit, minmax(320px, 1fr))",
                gap: "16px",
              }}
            >
              <TelemetryMiniChart title="Temperature Trend" series={historyByKey.get("tank_temp_main") ?? null} />
              <TelemetryMiniChart title="pH Trend" series={historyByKey.get("tank_ph_main") ?? null} />
              <TelemetryMiniChart title="Salinity Trend" series={historyByKey.get("tank_salinity_main") ?? null} />
              <TelemetryMiniChart title="Sump Level Trend" series={historyByKey.get("sump_level_main") ?? null} />
            </div>
          </>
        ) : null}
      </div>
    </div>
  );
}