import {
  CartesianGrid,
  Legend,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

import type { TelemetryHistoryResponse } from "../types";

type TelemetryChartProps = {
  history: TelemetryHistoryResponse;
};

type ChartRow = {
  timestamp: string;
  tank_temp_main?: number;
  tank_ph_main?: number;
  tank_salinity_main?: number;
  sump_level_main?: number;
};

function sensorLabel(sensorKey: string): string {
  switch (sensorKey) {
    case "tank_temp_main":
      return "Temperature";
    case "tank_ph_main":
      return "pH";
    case "tank_salinity_main":
      return "Salinity";
    case "sump_level_main":
      return "Sump Level";
    default:
      return sensorKey;
  }
}

export function TelemetryChart({ history }: TelemetryChartProps) {
  const rowsByTimestamp = new Map<string, ChartRow>();

  for (const series of history.series) {
    for (const point of series.points) {
      const existing = rowsByTimestamp.get(point.timestamp) ?? {
        timestamp: point.timestamp,
      };

      existing[series.sensor_key as keyof ChartRow] = point.value;
      rowsByTimestamp.set(point.timestamp, existing);
    }
  }

  const chartData = Array.from(rowsByTimestamp.values()).sort((a, b) =>
    a.timestamp.localeCompare(b.timestamp)
  );

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
        Telemetry Trends
      </div>

      <div style={{ width: "100%", height: 360 }}>
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
            <YAxis />
            <Tooltip
              labelFormatter={(value) => new Date(String(value)).toLocaleString()}
            />
            <Legend />
            <Line
              type="monotone"
              dataKey="tank_temp_main"
              name={sensorLabel("tank_temp_main")}
              dot={false}
              stroke="#1f77b4"
              strokeWidth={2}
            />
            <Line
              type="monotone"
              dataKey="tank_ph_main"
              name={sensorLabel("tank_ph_main")}
              dot={false}
              stroke="#2ca02c"
              strokeWidth={2}
            />
            <Line
              type="monotone"
              dataKey="tank_salinity_main"
              name={sensorLabel("tank_salinity_main")}
              dot={false}
              stroke="#ff7f0e"
              strokeWidth={2}
            />
            <Line
              type="monotone"
              dataKey="sump_level_main"
              name={sensorLabel("sump_level_main")}
              dot={false}
              stroke="#9467bd"
              strokeWidth={2}
            />
          </LineChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}