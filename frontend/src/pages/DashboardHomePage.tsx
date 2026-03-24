import { useEffect, useMemo, useState } from "react";

import {
  fetchAlerts,
  fetchSystemSummary,
  fetchTelemetryCatalog,
  fetchTelemetryHistory,
} from "../api/queries";
import AlertsSummaryCard from "../components/AlertsSummaryCard";
import type { RuntimeAlert } from "../types/alerts";
import type { SystemSummaryResponse, TelemetryHistoryResponse } from "../types";
import type {
  TelemetryCatalogItem,
  TelemetryCatalogResponse,
} from "../types/telemetryCatalog";

function sectionCard(children: React.ReactNode): JSX.Element {
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
      {children}
    </section>
  );
}

function categoryTitle(category: string): string {
  switch (category) {
    case "aquarium_core":
      return "Aquarium Core";
    case "water_quality":
      return "Water Quality";
    case "flow":
      return "Flow Monitoring";
    case "lighting":
      return "Lighting / PAR";
    case "safety":
      return "Leak & Safety";
    case "room_environment":
      return "Room Environment";
    case "power":
      return "Power Monitoring";
    default:
      return category;
  }
}

function latestReading(summary: SystemSummaryResponse | null, sensorKey: string) {
  return summary?.latest_readings.find((item) => item.sensor_key === sensorKey) ?? null;
}

function renderValue(
  summary: SystemSummaryResponse | null,
  history: TelemetryHistoryResponse | null,
  sensor: TelemetryCatalogItem
): { value: string; subtitle: string } {
  const live = latestReading(summary, sensor.sensor_key);

  if (live) {
    return {
      value: `${live.value} ${live.unit}`.trim(),
      subtitle: `Updated ${new Date(live.reading_time).toLocaleTimeString()}`,
    };
  }

  const series = history?.series?.[sensor.sensor_key] ?? [];
  const latestHistory = series.length > 0 ? series[series.length - 1] : null;

  if (latestHistory) {
    return {
      value: `${latestHistory.value} ${latestHistory.unit}`.trim(),
      subtitle: `History point ${new Date(latestHistory.timestamp).toLocaleTimeString()}`,
    };
  }

  return {
    value: "—",
    subtitle: "No reading available",
  };
}

function sensorCard(
  summary: SystemSummaryResponse | null,
  history: TelemetryHistoryResponse | null,
  sensor: TelemetryCatalogItem
): JSX.Element {
  const { value, subtitle } = renderValue(summary, history, sensor);

  return (
    <article
      key={sensor.sensor_key}
      style={{
        background: "#ffffff",
        border: "1px solid #e5e7eb",
        borderRadius: 16,
        padding: 18,
        boxShadow: "0 1px 3px rgba(0,0,0,0.06)",
      }}
    >
      <div style={{ fontSize: 13, color: "#6b7280", fontWeight: 700 }}>{sensor.label}</div>
      <div style={{ fontSize: 28, fontWeight: 800, marginTop: 10, color: "#111827" }}>{value}</div>
      <div style={{ fontSize: 13, color: "#6b7280", marginTop: 10 }}>{subtitle}</div>
      <div style={{ fontSize: 12, color: "#9ca3af", marginTop: 8 }}>{sensor.description}</div>
    </article>
  );
}

export default function DashboardHomePage() {
  const [summary, setSummary] = useState<SystemSummaryResponse | null>(null);
  const [history, setHistory] = useState<TelemetryHistoryResponse | null>(null);
  const [catalog, setCatalog] = useState<TelemetryCatalogResponse | null>(null);
  const [alerts, setAlerts] = useState<RuntimeAlert[]>([]);
  const [error, setError] = useState<string | null>(null);

  const generatedAt = useMemo(() => {
    if (!summary?.generated_at) {
      return "—";
    }

    return new Date(summary.generated_at).toLocaleString();
  }, [summary]);

  const groupedSensors = useMemo(() => {
    const items = catalog?.items ?? [];
    return items.reduce<Record<string, TelemetryCatalogItem[]>>((accumulator, item) => {
      if (!accumulator[item.category]) {
        accumulator[item.category] = [];
      }
      accumulator[item.category].push(item);
      return accumulator;
    }, {});
  }, [catalog]);

  useEffect(() => {
    let cancelled = false;

    async function load() {
      try {
        const [summaryResponse, historyResponse, catalogResponse, alertsResponse] =
          await Promise.all([
            fetchSystemSummary(),
            fetchTelemetryHistory(),
            fetchTelemetryCatalog(),
            fetchAlerts(),
          ]);

        if (!cancelled) {
          setSummary(summaryResponse);
          setHistory(historyResponse);
          setCatalog(catalogResponse);
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
    <div style={{ display: "grid", gap: 16, padding: 24, maxWidth: 1400, margin: "0 auto" }}>
      {sectionCard(
        <div>
          <h1 style={{ margin: 0, fontSize: 28 }}>Main Dashboard</h1>
          <p style={{ margin: "8px 0 0 0", color: "#4b5563" }}>
            Live system overview, environmental telemetry, platform health, expanded sensor visibility, and safety status.
          </p>
        </div>
      )}

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

      <AlertsSummaryCard alerts={alerts} />

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
          <article
            style={{
              border: "1px solid #d8dee4",
              borderRadius: 12,
              padding: 16,
              background: "#f9fafb",
            }}
          >
            <div style={{ fontSize: 12, color: "#6b7280", fontWeight: 700 }}>Timescale Extension</div>
            <div style={{ fontSize: 26, fontWeight: 800, marginTop: 8 }}>
              {summary?.timescale_status.extension_installed ? "Healthy" : "Missing"}
            </div>
          </article>

          <article
            style={{
              border: "1px solid #d8dee4",
              borderRadius: 12,
              padding: 16,
              background: "#f9fafb",
            }}
          >
            <div style={{ fontSize: 12, color: "#6b7280", fontWeight: 700 }}>Telemetry Hypertable</div>
            <div style={{ fontSize: 26, fontWeight: 800, marginTop: 8 }}>
              {summary?.timescale_status.telemetry_is_hypertable ? "Healthy" : "Check"}
            </div>
          </article>

          <article
            style={{
              border: "1px solid #d8dee4",
              borderRadius: 12,
              padding: 16,
              background: "#f9fafb",
            }}
          >
            <div style={{ fontSize: 12, color: "#6b7280", fontWeight: 700 }}>Generated</div>
            <div style={{ fontSize: 20, fontWeight: 800, marginTop: 8 }}>{generatedAt}</div>
          </article>
        </div>
      </section>

      {Object.entries(groupedSensors).map(([category, sensors]) => (
        <section
          key={category}
          style={{
            display: "grid",
            gap: 12,
          }}
        >
          <div style={{ fontSize: 20, fontWeight: 800, color: "#111827" }}>
            {categoryTitle(category)}
          </div>

          <div
            style={{
              display: "grid",
              gridTemplateColumns: "repeat(auto-fit, minmax(250px, 1fr))",
              gap: 16,
            }}
          >
            {sensors.map((sensor) => sensorCard(summary, history, sensor))}
          </div>
        </section>
      ))}
    </div>
  );
}