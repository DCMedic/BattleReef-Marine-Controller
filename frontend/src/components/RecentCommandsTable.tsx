import { useState } from "react";
import type { CSSProperties } from "react";

import type { CommandResponse } from "../types";

type RecentCommandsTableProps = {
  items: CommandResponse[];
};

function formatPayload(payload: Record<string, unknown>): string {
  try {
    return JSON.stringify(payload);
  } catch {
    return "Invalid payload";
  }
}

export function RecentCommandsTable({ items }: RecentCommandsTableProps) {
  const [isOpen, setIsOpen] = useState(false);

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
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          gap: "12px",
          marginBottom: isOpen ? "12px" : "0",
        }}
      >
        <div
          style={{
            fontSize: "1rem",
            fontWeight: 700,
            color: "#1f2328",
          }}
        >
          Recent Commands
        </div>

        <button
          type="button"
          onClick={() => setIsOpen((prev) => !prev)}
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
          {isOpen ? "Hide" : "Show"}
        </button>
      </div>

      {!isOpen ? (
        <div
          style={{
            marginTop: "8px",
            fontSize: "0.9rem",
            color: "#57606a",
          }}
        >
          {items.length} recent command{items.length === 1 ? "" : "s"} available.
        </div>
      ) : (
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
                <th style={headerCellStyle}>ID</th>
                <th style={headerCellStyle}>Requested</th>
                <th style={headerCellStyle}>Device</th>
                <th style={headerCellStyle}>Type</th>
                <th style={headerCellStyle}>Status</th>
                <th style={headerCellStyle}>Payload</th>
              </tr>
            </thead>
            <tbody>
              {items.length === 0 ? (
                <tr>
                  <td style={bodyCellStyle} colSpan={6}>
                    No recent commands available.
                  </td>
                </tr>
              ) : (
                items.map((item) => (
                  <tr key={item.id}>
                    <td style={bodyCellStyle}>{item.id}</td>
                    <td style={bodyCellStyle}>
                      {new Date(item.requested_at).toLocaleString()}
                    </td>
                    <td style={bodyCellStyle}>{item.target_device}</td>
                    <td style={bodyCellStyle}>{item.command_type}</td>
                    <td style={bodyCellStyle}>{item.status}</td>
                    <td style={bodyCellStyle}>{formatPayload(item.command_payload)}</td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}

const headerCellStyle: CSSProperties = {
  textAlign: "left",
  padding: "10px 8px",
  borderBottom: "1px solid #d8dee4",
  color: "#57606a",
  fontWeight: 700,
  whiteSpace: "nowrap",
};

const bodyCellStyle: CSSProperties = {
  padding: "10px 8px",
  borderBottom: "1px solid #d8dee4",
  color: "#1f2328",
  verticalAlign: "top",
};