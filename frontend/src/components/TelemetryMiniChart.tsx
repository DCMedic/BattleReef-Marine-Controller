import {
  CartesianGrid,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

import type { TelemetryHistorySeries } from "../types";

type TelemetryMiniChartProps = {
  title: string;
  series: TelemetryHistorySeries | null;
};

export function TelemetryMiniChart({ title, series }: TelemetryMiniChartProps) {
  const chartData =
    series?.points.map((point) => ({
      timestamp: point.timestamp,
      value: point.value,
    })) ?? [];

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
          marginBottom: "6px",
        }}
      >
        {title}
      </div>

      <div
        style={{
          fontSize: "0.85rem",
          color: "#57606a",
          marginBottom: "12px",
        }}
      >
        {series ? `Unit: ${series.unit}` : "No series available"}
      </div>

      <div style={{ width: "100%", height: 240 }}>
        <ResponsiveContainer>
          <LineChart data={chartData}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis
              dataKey="timestamp"
              tickFormatter={(value) =>
                new Date(value).toLocaleTimeString([], {
                  hour: "2-digit",
                  minute: "2-digit",
                })
              }
            />
            <YAxis domain={["auto", "auto"]} />
            <Tooltip
              labelFormatter={(value) => new Date(String(value)).toLocaleString()}
            />
            <Line
              type="monotone"
              dataKey="value"
              dot={false}
              stroke="#1f77b4"
              strokeWidth={2}
            />
          </LineChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}