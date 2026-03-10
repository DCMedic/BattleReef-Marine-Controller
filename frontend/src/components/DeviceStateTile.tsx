import type { DeviceStateSummary } from "../types";

type DeviceStateTileProps = {
  item: DeviceStateSummary;
};

function formatValue(value: unknown): string {
  if (typeof value === "boolean") return value ? "True" : "False";
  if (value === null || value === undefined) return "N/A";
  return String(value);
}

export function DeviceStateTile({ item }: DeviceStateTileProps) {
  const entries = Object.entries(item.state_payload ?? {});

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
          marginBottom: "8px",
        }}
      >
        {item.device_key}
      </div>

      <div
        style={{
          fontSize: "0.85rem",
          color: "#57606a",
          marginBottom: "12px",
        }}
      >
        Source: {item.state_source}
      </div>

      <div
        style={{
          display: "grid",
          gap: "8px",
        }}
      >
        {entries.length === 0 ? (
          <div style={{ color: "#656d76", fontSize: "0.9rem" }}>No state data available.</div>
        ) : (
          entries.map(([key, value]) => (
            <div
              key={key}
              style={{
                display: "flex",
                justifyContent: "space-between",
                gap: "12px",
                fontSize: "0.9rem",
              }}
            >
              <span style={{ color: "#57606a", fontWeight: 600 }}>{key}</span>
              <span style={{ color: "#1f2328" }}>{formatValue(value)}</span>
            </div>
          ))
        )}
      </div>

      <div
        style={{
          marginTop: "12px",
          fontSize: "0.8rem",
          color: "#656d76",
        }}
      >
        Updated: {new Date(item.updated_at).toLocaleString()}
      </div>
    </div>
  );
}