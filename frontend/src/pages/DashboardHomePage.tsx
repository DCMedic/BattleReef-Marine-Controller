import { useEffect, useMemo, useState } from "react";

import { fetchTelemetryCatalog, fetchTelemetryHistory } from "../api/queries";
import AlertsSummaryCard from "../components/AlertsSummaryCard";
import LiveStreamStatusCard from "../components/LiveStreamStatusCard";
import { useBattleReefEventStream } from "../hooks/useBattleReefEventStream";
import type { TelemetryHistoryResponse } from "../types";
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

function latestReading(summary: any, sensorKey: string) {
  return summary?.latest_readings?.find((item: any) => item.sensor_key === sensorKey) ?? null;
}

function readingTone(sensorKey: string, valueRaw: string): React.CSSProperties {
  const numericValue = Number(valueRaw);

  if (sensorKey.startsWith("leak_probe")) {
    const normal = valueRaw.toLowerCase() === "dry";
    return normal
      ? { borderColor: "#a7f3d0", background: "#ecfdf5" }
      : { borderColor: "#fecdd3", background: "#fff1f2" };
  }

  if (!Number.isNaN(numericValue)) {
    if (sensorKey === "dissolved_oxygen_main" && numericValue < 6) {
      return { borderColor: "#fecdd3", background: "#fff1f2" };
    }
    if (sensorKey === "room_co2_main" && numericValue > 1200) {
      return { borderColor: "#fde68a", background: "#fffbeb" };
    }
    if (sensorKey === "flow_return_main" && numericValue < 500) {
      return { borderColor: "#fecdd3", background: "#fff1f2" };
    }
    if (sensorKey === "flow_manifold_main" && numericValue < 150) {
      return { borderColor: "#fde68a", background: "#fffbeb" };
    }
  }

  return { borderColor: "#e5e7eb", background: "#ffffff" };
}

function renderValue(
  summary: any,
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
  summary: any,
  history: TelemetryHistoryResponse | null,
  sensor: TelemetryCatalogItem
): JSX.Element {
  const { value, subtitle } = renderValue(summary, history, sensor);
  const tone = readingTone(sensor.sensor_key, value.split(" ")[0] ?? value);

  return (
    <article
      key={sensor.sensor_key}
      style={{
        border: `1px solid ${tone.borderColor}`,
        background: tone.background,
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
  const [history, setHistory] = useState<TelemetryHistoryResponse | null>(null);
  const [catalog, setCatalog] = useState<TelemetryCatalogResponse | null>(null);
  const [fallbackError, setFallbackError] = useState<string | null>(null);

  const { snapshot, connected, error: streamError } = useBattleReefEventStream();

  const summary = snapshot?.summary ?? null;
  const alerts = snapshot?.alerts ?? [];

  const generatedAt = useMemo(() => {
    if (!summary?.generated_at) {
      return "—";
    }

    return new Date(summary.generated_at).toLocaleString();
  }, [summary]);

  const lastUpdated = useMemo(() => {
    if (!snapshot?.timestamp) {
      return null;
    }

    return new Date(snapshot.timestamp).toLocaleString();
  }, [snapshot]);

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

    async function loadStaticData() {
      try {
        const [historyResponse, catalogResponse] = await Promise.all([
          fetchTelemetryHistory(),
          fetchTelemetryCatalog(),
        ]);

        if (!cancelled) {
          setHistory(historyResponse);
          setCatalog(catalogResponse);
          setFallbackError(null);
        }
      } catch (err) {
        if (!cancelled) {
          setFallbackError(err instanceof Error ? err.message : "Failed to load dashboard support data");
        }
      }
    }

    void loadStaticData();

    const timer = window.setInterval(() => {
      void loadStaticData();
    }, 15000);

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

      <LiveStreamStatusCard connected={connected} lastUpdated={lastUpdated} error={streamError} />

      {fallbackError ? (
        <section
          style={{
            background: "#fff1f2",
            border: "1px solid #fecdd3",
            borderRadius: 16,
            padding: 16,
            color: "#9f1239",
          }}
        >
          {fallbackError}
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
              {summary?.timescale_status?.extension_installed ? "Healthy" : "Missing"}
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
              {summary?.timescale_status?.telemetry_is_hypertable ? "Healthy" : "Check"}
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