export interface TelemetryWindowPoint {
  timestamp: string;
  value: number;
}

export interface TelemetryWindowResponse {
  sensor_key: string;
  unit: string | null;
  days: number;
  max_points: number;
  points: TelemetryWindowPoint[];
  latest_value: number | null;
  latest_timestamp: string | null;
  min_value: number | null;
  max_value: number | null;
}