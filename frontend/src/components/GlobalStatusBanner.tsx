import { useEffect, useMemo, useState } from "react";

import { fetchAlerts, fetchSystemSummary } from "../api/queries";
import type { AlertsListResponse, RuntimeAlert } from "../types/alerts";
import type { SystemSummaryResponse } from "../types";

function bannerPalette(tone: "danger" | "warning" | "success" | "default") {
  if (tone === "danger") {
    return {
      background: "#fff1f2",
      border: "#fecdd3",
      color: "#9f1239",
    };
  }

  if (tone === "warning") {
    return {
      background: "#fffbeb",
      border: "#fde68a",
      color: "#92400e",
    };
  }

  if (tone === "success") {
    return {
      background: "#ecfdf5",
      border: "#a7f3d0",
      color: "#065f46",
    };
  }

  return {
    background: "#f9fafb",
    border: "#e5e7eb",
    color: "#374151",
  };
}

function selectTopAlert(alerts: RuntimeAlert[]): RuntimeAlert | null {
  const critical = alerts.find((alert) => alert.severity === "critical");
  if (critical) {
    return critical;
  }

  const warning = alerts.find((alert) => alert.severity === "warning");
  if (warning) {
    return warning;
  }

  return alerts[0] ?? null;
}

export default function GlobalStatusBanner() {
  const [summary, setSummary] = useState<SystemSummaryResponse | null>(null);
  const [alerts, setAlerts] = useState<AlertsListResponse | null>(null);
  const [reachable, setReachable] = useState(true);

  useEffect(() => {
    let cancelled = false;

    async function load() {
      try {
        const [summaryResponse, alertsResponse] = await Promise.all([
          fetchSystemSummary(),
          fetchAlerts(),
        ]);

        if (!cancelled) {
          setSummary(summaryResponse);
          setAlerts(alertsResponse);
          setReachable(true);
        }
      } catch {
        if (!cancelled) {
          setReachable(false);
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

  const alertItems = alerts?.items ?? [];
  const criticalCount = useMemo(
    () => alertItems.filter((alert) => alert.severity === "critical").length,
    [alertItems]
  );
  const warningCount = useMemo(
    () => alertItems.filter((alert) => alert.severity === "warning").length,
    [alertItems]
  );
  const topAlert = useMemo(() => selectTopAlert(alertItems), [alertItems]);

  const platformHealthy =
    summary?.timescale_status.extension_installed &&
    summary?.timescale_status.telemetry_is_hypertable;

  const tone: "danger" | "warning" | "success" | "default" = !reachable
    ? "danger"
    : criticalCount > 0
    ? "danger"
    : warningCount > 0 || !platformHealthy
    ? "warning"
    : "success";

  const palette = bannerPalette(tone);

  const headline = !reachable
    ? "Backend connectivity problem detected"
    : criticalCount > 0
    ? `Critical alerts active: ${criticalCount}`
    : warningCount > 0
    ? `Warning alerts active: ${warningCount}`
    : platformHealthy
    ? "Platform healthy"
    : "Platform degraded";

  const detail = !reachable
    ? "The frontend could not reach the backend API during the latest refresh cycle."
    : topAlert
    ? `${topAlert.title}: ${topAlert.message}`
    : platformHealthy
    ? "Telemetry, Timescale, and core platform services are reporting normal status."
    : "The platform is reachable, but one or more core health signals are degraded.";

  return (
    <section
      style={{
        borderBottom: `1px solid ${palette.border}`,
        background: palette.background,
        color: palette.color,
        padding: "12px 24px",
      }}
    >
      <div
        style={{
          maxWidth: "1400px",
          margin: "0 auto",
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          gap: 16,
          flexWrap: "wrap",
        }}
      >
        <div style={{ display: "grid", gap: 4 }}>
          <div style={{ fontWeight: 800, fontSize: "0.95rem" }}>{headline}</div>
          <div style={{ fontSize: "0.82rem", lineHeight: 1.5 }}>{detail}</div>
        </div>

        <div
          style={{
            display: "flex",
            gap: 10,
            flexWrap: "wrap",
            alignItems: "center",
          }}
        >
          <span
            style={{
              border: `1px solid ${palette.border}`,
              borderRadius: 999,
              padding: "4px 10px",
              fontSize: 12,
              fontWeight: 800,
              background: "#ffffff80",
            }}
          >
            API: {reachable ? "Connected" : "Disconnected"}
          </span>

          <span
            style={{
              border: `1px solid ${palette.border}`,
              borderRadius: 999,
              padding: "4px 10px",
              fontSize: 12,
              fontWeight: 800,
              background: "#ffffff80",
            }}
          >
            Critical: {criticalCount}
          </span>

          <span
            style={{
              border: `1px solid ${palette.border}`,
              borderRadius: 999,
              padding: "4px 10px",
              fontSize: 12,
              fontWeight: 800,
              background: "#ffffff80",
            }}
          >
            Warning: {warningCount}
          </span>
        </div>
      </div>
    </section>
  );
}