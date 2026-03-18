import { useEffect, useMemo, useState } from "react";

import { fetchAlerts, fetchSystemSummary, fetchTelemetryHistory } from "../api/queries";
import AlertsSummaryCard from "../components/AlertsSummaryCard";
import type { RuntimeAlert } from "../types/alerts";
import type { SystemSummaryResponse, TelemetryHistoryResponse } from "../types";

function metricCard(title: string, value: string, subtitle: string) {
  return (
    <section
      style={{
        background: "#ffffff",
        border: "1px solid #e5e7eb",
        borderRadius: 16,
        padding: 20,
        boxShadow: "0 1px 3px rgba(0,0,0,0.06)",
      }}
    >
      <div style={{ color: "#6b7280", fontSize: 13 }}>{title}</div>
      <div style={{ fontSize: 28, fontWeight: 800, marginTop: 8 }}>{value}</div>
      <div style={{ color: "#6b7280", fontSize: 13, marginTop: 8 }}>{subtitle}</div>
    </section>
  );
}

function latestReadingValue(
  summary: SystemSummaryResponse | null,
  sensorKey: string,
  fallbackUnit = ""
): string {
  const reading = summary?.latest_readings.find((item) => item.sensor_key === sensorKey);

  if (!reading) {
    return "—";
  }

  return `${reading.value} ${reading.unit || fallbackUnit}`.trim();
}

function latestReadingTime(
  summary: SystemSummaryResponse | null,
  sensorKey: string
): string {
  const reading = summary?.latest_readings.find((item) => item.sensor_key === sensorKey);

  if (!reading) {
    return "No recent reading";
  }

  return `Updated ${new Date(reading.reading_time).toLocaleTimeString()}`;
}

export default function DashboardHomePage() {
  const [summary, setSummary] = useState<SystemSummaryResponse | null>(null);
  const [history, setHistory] = useState<TelemetryHistoryResponse | null>(null);
  const [alerts, setAlerts] = useState<RuntimeAlert[]>([]);
  const [error, setError] = useState<string | null>(null);

  const generatedAt = useMemo(() => {
    if (!summary?.generated_at) {
      return "—";
    }

    return new Date(summary.generated_at).toLocaleString();
  }, [summary]);

  useEffect(() => {
    let cancelled = false;

    async function load() {
      try {
        const [summaryResponse, historyResponse, alertsResponse] = await Promise.all([
          fetchSystemSummary(),
          fetchTelemetryHistory(),
          fetchAlerts(),
        ]);

        if (!cancelled) {
          setSummary(summaryResponse);
          setHistory(historyResponse);
          setAlerts(alertsResponse.items);
          setError(null);
        }
      } catch (err) {
        if (!cancelled) {
          setError(err instanceof Error ? err.message : "Failed to load dashboard");
        }
      }
    }

    void load();

    const timer = window.setInterval(() => {
      void load();
    }, 5000);

    return () => {
      cancelled = true;
      window.clearInterval(timer);
    };
  }, []);

  return (
    <div style={{ display: "grid", gap: 16 }}>
      <section
        style={{
          background: "#ffffff",
          border: "1px solid #e5e7eb",
          borderRadius: 16,
          padding: 20,
          boxShadow: "0 1px 3px rgba(0,0,0,0.06)",
        }}
      >
        <h1 style={{ margin: 0, fontSize: 28 }}>Main Dashboard</h1>
        <p style={{ margin: "8px 0 0 0", color: "#4b5563" }}>
          Live system overview, environmental telemetry, platform health, trend visibility, and safety status.
        </p>
      </section>

      {error ? (
        <section
          style={{
            background: "#fff1f2",
            border: "1px solid #fecdd3",
            borderRadius: 16,
            padding: 16,
            color: "#9f1239",
          }}
        >
          {error}
        </section>
      ) : null}

      <div
        style={{
          display: "grid",
          gridTemplateColumns: "repeat(4, minmax(0, 1fr))",
          gap: 16,
        }}
      >
        {metricCard(
          "Temperature",
          latestReadingValue(summary, "tank_temp_main", "F"),
          latestReadingTime(summary, "tank_temp_main")
        )}
        {metricCard(
          "pH",
          latestReadingValue(summary, "tank_ph_main", "pH"),
          latestReadingTime(summary, "tank_ph_main")
        )}
        {metricCard(
          "Salinity",
          latestReadingValue(summary, "tank_salinity_main", "ppt"),
          latestReadingTime(summary, "tank_salinity_main")
        )}
        {metricCard(
          "Sump Level",
          latestReadingValue(summary, "sump_level_main", "in"),
          latestReadingTime(summary, "sump_level_main")
        )}
      </div>

      <AlertsSummaryCard alerts={alerts} />

      <div
        style={{
          display: "grid",
          gridTemplateColumns: "repeat(4, minmax(0, 1fr))",
          gap: 16,
        }}
      >
        {metricCard(
          "Telemetry Records",
          String(summary?.counts.telemetry_readings ?? "—"),
          "Total ingested readings"
        )}
        {metricCard(
          "Commands Completed",
          String(summary?.counts.commands_completed ?? "—"),
          "Successfully completed command executions"
        )}
        {metricCard(
          "Commands Failed",
          String(summary?.counts.commands_failed ?? "—"),
          "Failed command executions"
        )}
        {metricCard(
          "Tracked Devices",
          String(summary?.counts.device_states ?? "—"),
          "Devices with persisted state"
        )}
      </div>

      <section
        style={{
          background: "#ffffff",
          border: "1px solid #e5e7eb",
          borderRadius: 16,
          padding: 20,
          boxShadow: "0 1px 3px rgba(0,0,0,0.06)",
        }}
      >
        <div style={{ fontWeight: 700, marginBottom: 12 }}>Platform Status</div>

        <div
          style={{
            display: "grid",
            gridTemplateColumns: "repeat(3, minmax(0, 1fr))",
            gap: 16,
          }}
        >
          {metricCard(
            "Timescale Extension",
            summary?.timescale_status.extension_installed ? "Healthy" : "Missing",
            "Database extension status"
          )}
          {metricCard(
            "Telemetry Hypertable",
            summary?.timescale_status.telemetry_is_hypertable ? "Healthy" : "Check",
            "Timescale hypertable status"
          )}
          {metricCard("Generated", generatedAt, "Latest summary refresh")}
        </div>
      </section>

      <section
        style={{
          background: "#ffffff",
          border: "1px solid #e5e7eb",
          borderRadius: 16,
          padding: 20,
          boxShadow: "0 1px 3px rgba(0,0,0,0.06)",
        }}
      >
        <div style={{ fontWeight: 700, marginBottom: 12 }}>Telemetry History Status</div>
        <div style={{ color: "#4b5563" }}>
          Loaded telemetry series: {history ? Object.keys(history.series).length : 0}
        </div>
      </section>
    </div>
  );
}