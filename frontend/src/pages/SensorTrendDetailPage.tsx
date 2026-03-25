import { useEffect, useMemo, useState } from "react";
import { Link, useParams } from "react-router-dom";

import {
  fetchTelemetryCatalog,
  fetchTelemetryWindow,
  fetchThresholds,
} from "../api/queries";
import TelemetryLineChart from "../components/TelemetryLineChart";
import type { TelemetryCatalogResponse } from "../types/telemetryCatalog";
import type { ThresholdListResponse } from "../types/thresholds";
import type { TelemetryWindowResponse } from "../types/telemetryTrends";

export default function SensorTrendDetailPage() {
  const { sensorKey = "" } = useParams();

  const [catalog, setCatalog] = useState<TelemetryCatalogResponse | null>(null);
  const [thresholds, setThresholds] = useState<ThresholdListResponse | null>(null);
  const [windowData, setWindowData] = useState<TelemetryWindowResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;

    async function load() {
      try {
        const [catalogResponse, thresholdResponse, telemetryResponse] = await Promise.all([
          fetchTelemetryCatalog(),
          fetchThresholds(),
          fetchTelemetryWindow(sensorKey, 365, 365),
        ]);

        if (!cancelled) {
          setCatalog(catalogResponse);
          setThresholds(thresholdResponse);
          setWindowData(telemetryResponse);
          setError(null);
        }
      } catch (err) {
        if (!cancelled) {
          setError(err instanceof Error ? err.message : "Failed to load trend detail");
        }
      }
    }

    if (sensorKey) {
      void load();
    }

    return () => {
      cancelled = true;
    };
  }, [sensorKey]);

  const sensor = useMemo(
    () => catalog?.items.find((item) => item.sensor_key === sensorKey) ?? null,
    [catalog, sensorKey]
  );

  const threshold = useMemo(
    () => thresholds?.items.find((item) => item.sensor_key === sensorKey) ?? null,
    [thresholds, sensorKey]
  );

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
        <div style={{ display: "flex", justifyContent: "space-between", gap: 12, flexWrap: "wrap" }}>
          <div>
            <h1 style={{ margin: 0, fontSize: 28 }}>
              {sensor?.label ?? sensorKey} Trend Detail
            </h1>
            <p style={{ margin: "8px 0 0 0", color: "#4b5563", lineHeight: 1.6 }}>
              Full-year graph view with threshold overlays and daily-resolution history.
            </p>
          </div>

          <Link
            to="/sensor-trends"
            style={{
              alignSelf: "start",
              textDecoration: "none",
              border: "1px solid #d1d5db",
              borderRadius: 10,
              padding: "10px 14px",
              color: "#111827",
              fontWeight: 700,
              background: "#ffffff",
            }}
          >
            Back to Sensor Trends
          </Link>
        </div>
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

      <section
        style={{
          background: "#ffffff",
          border: "1px solid #e5e7eb",
          borderRadius: 16,
          padding: 20,
          boxShadow: "0 1px 3px rgba(0,0,0,0.06)",
          display: "grid",
          gap: 16,
        }}
      >
        <div style={{ display: "grid", gap: 8 }}>
          <div style={{ fontSize: 20, fontWeight: 800, color: "#111827" }}>
            365-Day History
          </div>
          <div style={{ color: "#6b7280" }}>
            Unit: {windowData?.unit ?? sensor?.unit ?? "—"} ·
            Latest:{" "}
            {windowData?.latest_value !== null && windowData?.latest_value !== undefined
              ? `${windowData.latest_value} ${windowData.unit ?? ""}`.trim()
              : "No data"}
          </div>
        </div>

        <TelemetryLineChart
          points={windowData?.points ?? []}
          threshold={{
            min: typeof threshold?.min === "number" ? threshold.min : null,
            max: typeof threshold?.max === "number" ? threshold.max : null,
            severity: threshold?.severity,
          }}
          height={360}
        />

        <div
          style={{
            display: "grid",
            gridTemplateColumns: "repeat(4, minmax(0, 1fr))",
            gap: 12,
          }}
        >
          <div
            style={{
              border: "1px solid #e5e7eb",
              borderRadius: 12,
              padding: 14,
              background: "#f9fafb",
            }}
          >
            <div style={{ fontSize: 12, color: "#6b7280", fontWeight: 700 }}>Minimum Threshold</div>
            <div style={{ marginTop: 8, fontSize: 24, fontWeight: 800 }}>
              {threshold?.min ?? "Disabled"}
            </div>
          </div>

          <div
            style={{
              border: "1px solid #e5e7eb",
              borderRadius: 12,
              padding: 14,
              background: "#f9fafb",
            }}
          >
            <div style={{ fontSize: 12, color: "#6b7280", fontWeight: 700 }}>Maximum Threshold</div>
            <div style={{ marginTop: 8, fontSize: 24, fontWeight: 800 }}>
              {threshold?.max ?? "Disabled"}
            </div>
          </div>

          <div
            style={{
              border: "1px solid #e5e7eb",
              borderRadius: "12px",
              padding: 14,
              background: "#f9fafb",
            }}
          >
            <div style={{ fontSize: 12, color: "#6b7280", fontWeight: 700 }}>Observed Minimum</div>
            <div style={{ marginTop: 8, fontSize: 24, fontWeight: 800 }}>
              {windowData?.min_value ?? "—"}
            </div>
          </div>

          <div
            style={{
              border: "1px solid #e5e7eb",
              borderRadius: 12,
              padding: 14,
              background: "#f9fafb",
            }}
          >
            <div style={{ fontSize: 12, color: "#6b7280", fontWeight: 700 }}>Observed Maximum</div>
            <div style={{ marginTop: 8, fontSize: 24, fontWeight: 800 }}>
              {windowData?.max_value ?? "—"}
            </div>
          </div>
        </div>
      </section>
    </div>
  );
}