import type { RuntimeAlert } from "../types/alerts";

type Props = {
  alerts: RuntimeAlert[];
};

export default function AlertsSummaryCard({ alerts }: Props) {
  const criticalCount = alerts.filter((alert) => alert.severity === "critical").length;
  const warningCount = alerts.filter((alert) => alert.severity === "warning").length;

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
      <div style={{ fontWeight: 700, marginBottom: 12 }}>Safety Status</div>

      <div style={{ display: "grid", gridTemplateColumns: "repeat(3, minmax(0, 1fr))", gap: 12 }}>
        <div
          style={{
            borderRadius: 12,
            padding: 14,
            background: "#f9fafb",
            border: "1px solid #e5e7eb",
          }}
        >
          <div style={{ fontSize: 12, color: "#6b7280" }}>Active Alerts</div>
          <div style={{ fontSize: 28, fontWeight: 700 }}>{alerts.length}</div>
        </div>

        <div
          style={{
            borderRadius: 12,
            padding: 14,
            background: "#fff1f2",
            border: "1px solid #fecdd3",
          }}
        >
          <div style={{ fontSize: 12, color: "#9f1239" }}>Critical</div>
          <div style={{ fontSize: 28, fontWeight: 700, color: "#9f1239" }}>{criticalCount}</div>
        </div>

        <div
          style={{
            borderRadius: 12,
            padding: 14,
            background: "#fffbeb",
            border: "1px solid #fde68a",
          }}
        >
          <div style={{ fontSize: 12, color: "#92400e" }}>Warning</div>
          <div style={{ fontSize: 28, fontWeight: 700, color: "#92400e" }}>{warningCount}</div>
        </div>
      </div>
    </section>
  );
}