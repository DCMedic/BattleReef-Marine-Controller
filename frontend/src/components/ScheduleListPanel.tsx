import { useEffect, useState } from "react";

import { fetchSchedules, seedDefaultSchedules } from "../api/queries";
import type { ScheduleResponse } from "../types";

type ScheduleListPanelProps = {
  refreshToken?: number;
};

export function ScheduleListPanel({ refreshToken = 0 }: ScheduleListPanelProps) {
  const [items, setItems] = useState<ScheduleResponse[]>([]);
  const [message, setMessage] = useState("");
  const [busy, setBusy] = useState(false);

  async function loadSchedules() {
    try {
      const data = await fetchSchedules();
      setItems(data.items);
      setMessage("");
    } catch (error) {
      const text = error instanceof Error ? error.message : "Failed to load schedules";
      setMessage(text);
    }
  }

  useEffect(() => {
    void loadSchedules();
  }, [refreshToken]);

  async function handleSeedDefaults() {
    try {
      setBusy(true);
      const data = await seedDefaultSchedules();
      setItems(data.items);
      setMessage("Default schedules loaded.");
    } catch (error) {
      const text = error instanceof Error ? error.message : "Failed to seed schedules";
      setMessage(text);
    } finally {
      setBusy(false);
    }
  }

  return (
    <div
      style={{
        border: "1px solid #d0d7de",
        borderRadius: "12px",
        padding: "16px",
        background: "#ffffff",
        boxShadow: "0 1px 3px rgba(0,0,0,0.06)",
        marginBottom: "24px",
      }}
    >
      <div
        style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          gap: "12px",
          marginBottom: "12px",
        }}
      >
        <div
          style={{
            fontSize: "1rem",
            fontWeight: 700,
            color: "#1f2328",
          }}
        >
          Schedule Configuration
        </div>

        <button
          type="button"
          disabled={busy}
          onClick={handleSeedDefaults}
          style={{
            border: "1px solid #d0d7de",
            borderRadius: "8px",
            background: "#f6f8fa",
            color: "#1f2328",
            padding: "8px 12px",
            fontSize: "0.9rem",
            fontWeight: 600,
            cursor: "pointer",
          }}
        >
          Seed Defaults
        </button>
      </div>

      <div
        style={{
          minHeight: "20px",
          marginBottom: "12px",
          fontSize: "0.85rem",
          color:
            message.toLowerCase().includes("failed") || message.toLowerCase().includes("error")
              ? "#cf222e"
              : "#1a7f37",
        }}
      >
        {message}
      </div>

      <div style={{ overflowX: "auto" }}>
        <table
          style={{
            width: "100%",
            borderCollapse: "collapse",
            fontSize: "0.9rem",
          }}
        >
          <thead>
            <tr>
              <th style={headerCell}>ID</th>
              <th style={headerCell}>Device</th>
              <th style={headerCell}>Type</th>
              <th style={headerCell}>Name</th>
              <th style={headerCell}>Enabled</th>
              <th style={headerCell}>Config</th>
            </tr>
          </thead>
          <tbody>
            {items.length === 0 ? (
              <tr>
                <td style={bodyCell} colSpan={6}>
                  No schedules configured.
                </td>
              </tr>
            ) : (
              items.map((item) => (
                <tr key={item.id}>
                  <td style={bodyCell}>{item.id}</td>
                  <td style={bodyCell}>{item.device_key}</td>
                  <td style={bodyCell}>{item.schedule_type}</td>
                  <td style={bodyCell}>{item.name}</td>
                  <td style={bodyCell}>{item.enabled ? "True" : "False"}</td>
                  <td style={bodyCell}>{JSON.stringify(item.config_payload)}</td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}

const headerCell: React.CSSProperties = {
  textAlign: "left",
  padding: "10px 8px",
  borderBottom: "1px solid #d8dee4",
  color: "#57606a",
  fontWeight: 700,
  whiteSpace: "nowrap",
};

const bodyCell: React.CSSProperties = {
  padding: "10px 8px",
  borderBottom: "1px solid #d8dee4",
  color: "#1f2328",
  verticalAlign: "top",
};