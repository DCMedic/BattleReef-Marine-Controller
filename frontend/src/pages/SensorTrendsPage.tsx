import { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";

import {
  fetchTelemetryCatalog,
  fetchTelemetryWindow,
  fetchThresholds,
} from "../api/queries";
import TelemetryLineChart from "../components/TelemetryLineChart";
import type { TelemetryCatalogResponse } from "../types/telemetryCatalog";
import type { ThresholdListResponse } from "../types/thresholds";
import type { TelemetryWindowResponse } from "../types/telemetryTrends";

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

function formatLatest(windowData: TelemetryWindowResponse): string {
  if (windowData.latest_value === null) {
    return "No recent value";
  }
  return `${windowData.latest_value} ${windowData.unit ?? ""}`.trim();
}

export default function SensorTrendsPage() {
  const [catalog, setCatalog] = useState<TelemetryCatalogResponse | null>(null);
  const [thresholds, setThresholds] = useState<ThresholdListResponse | null>(null);
  const [windows, setWindows] = useState<Record<string, TelemetryWindowResponse>>({});
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;

    async function load() {
      try {
        const [catalogResponse, thresholdResponse] = await Promise.all([
          fetchTelemetryCatalog(),
          fetchThresholds(),
        ]);

        if (cancelled) {
          return;
        }

        setCatalog(catalogResponse);
        setThresholds(thresholdResponse);

        const results = await Promise.all(
          catalogResponse.items.map(async (sensor) => {
            const windowData = await fetchTelemetryWindow(sensor.sensor_key, 3, 288);
            return [sensor.sensor_key, windowData] as const;
          })
        );

        if (!cancelled) {
          setWindows(Object.fromEntries(results));
          setError(null);
        }
      } catch (err) {
        if (!cancelled) {
          setError(err instanceof Error ? err.message : "Failed to load sensor trends");
        }
      }
    }

    void load();

    const timer = window.setInterval(() => {
      void load();
    }, 15000);

    return () => {
      cancelled = true;
      window.clearInterval(timer);
    };
  }, []);

  const groupedSensors = useMemo(() => {
    const items = catalog?.items ?? [];
    return items.reduce<Record<string, typeof items>>((accumulator, item) => {
      if (!accumulator[item.category]) {
        accumulator[item.category] = [];
      }
      accumulator[item.category].push(item);
      return accumulator;
    }, {});
  }, [catalog]);

  const thresholdMap = useMemo(() => {
    const items = thresholds?.items ?? [];
    return Object.fromEntries(items.map((item) => [item.sensor_key, item]));
  }, [thresholds]);

  return (
    <div style={{ display: "grid", gap: 16, padding: 24, maxWidth: 1500, margin: "0 auto" }}>
      <section
        style={{
          background: "#ffffff",
          border: "1px solid #e5e7eb",
          borderRadius: 16,
          padding: 20,
          boxShadow: "0 1px 3px rgba(0,0,0,0.06)",
        }}
      >
        <h1 style={{ margin: 0, fontSize: 28 }}>Sensor Trends</h1>
        <p style={{ margin: "8px 0 0 0", color: "#4b5563", lineHeight: 1.6 }}>
          Three-day trend views for every sensor in the system. Click any graph to open a full
          365-day detail page.
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

      {Object.entries(groupedSensors).map(([category, sensors]) => (
        <section key={category} style={{ display: "grid", gap: 12 }}>
          <div style={{ fontSize: 22, fontWeight: 800, color: "#111827" }}>
            {categoryTitle(category)}
          </div>

          <div
            style={{
              display: "grid",
              gridTemplateColumns: "repeat(auto-fit, minmax(360px, 1fr))",
              gap: 16,
            }}
          >
            {sensors.map((sensor) => {
              const windowData = windows[sensor.sensor_key];
              const threshold = thresholdMap[sensor.sensor_key];

              return (
                <Link
                  key={sensor.sensor_key}
                  to={`/sensor-trends/${sensor.sensor_key}`}
                  style={{ textDecoration: "none", color: "inherit" }}
                >
                  <article
                    style={{
                      background: "#ffffff",
                      border: "1px solid #e5e7eb",
                      borderRadius: 16,
                      padding: 16,
                      boxShadow: "0 1px 3px rgba(0,0,0,0.06)",
                      display: "grid",
                      gap: 12,
                      cursor: "pointer",
                    }}
                  >
                    <div>
                      <div style={{ fontSize: 18, fontWeight: 800, color: "#111827" }}>
                        {sensor.label}
                      </div>
                      <div style={{ color: "#6b7280", marginTop: 4 }}>
                        Latest: {windowData ? formatLatest(windowData) : "Loading..."}
                      </div>
                    </div>

                    <TelemetryLineChart
                      points={windowData?.points ?? []}
                      threshold={{
                        min: typeof threshold?.min === "number" ? threshold.min : null,
                        max: typeof threshold?.max === "number" ? threshold.max : null,
                        severity: threshold?.severity,
                      }}
                      height={180}
                    />

                    <div style={{ fontSize: 13, color: "#6b7280" }}>
                      Default window: 3 days · Click for 365-day detail
                    </div>
                  </article>
                </Link>
              );
            })}
          </div>
        </section>
      ))}
    </div>
  );
}