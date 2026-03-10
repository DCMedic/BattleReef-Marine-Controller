import type { SystemSummaryResponse } from "../types";

type SystemStatusPanelProps = {
  summary: SystemSummaryResponse;
};

function statusText(value: boolean): string {
  return value ? "Healthy" : "Attention Needed";
}

function statusColor(value: boolean): string {
  return value ? "#1a7f37" : "#cf222e";
}

export function SystemStatusPanel({ summary }: SystemStatusPanelProps) {
  const extOk = summary.timescale_status.extension_installed;
  const hyperOk = summary.timescale_status.telemetry_is_hypertable;

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
          fontSize: "1rem",
          fontWeight: 700,
          color: "#1f2328",
          marginBottom: "12px",
        }}
      >
        Platform Status
      </div>

      <div style={{ display: "grid", gap: "10px" }}>
        <div style={{ display: "flex", justifyContent: "space-between", gap: "12px" }}>
          <span style={{ color: "#57606a", fontWeight: 600 }}>Timescale Extension</span>
          <span style={{ color: statusColor(extOk), fontWeight: 700 }}>{statusText(extOk)}</span>
        </div>

        <div style={{ display: "flex", justifyContent: "space-between", gap: "12px" }}>
          <span style={{ color: "#57606a", fontWeight: 600 }}>Telemetry Hypertable</span>
          <span style={{ color: statusColor(hyperOk), fontWeight: 700 }}>{statusText(hyperOk)}</span>
        </div>

        <div style={{ display: "flex", justifyContent: "space-between", gap: "12px" }}>
          <span style={{ color: "#57606a", fontWeight: 600 }}>Generated</span>
          <span style={{ color: "#1f2328" }}>
            {new Date(summary.generated_at).toLocaleString()}
          </span>
        </div>
      </div>
    </div>
  );
}