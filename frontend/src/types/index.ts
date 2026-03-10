export type SystemCounts = {
  telemetry_readings: number;
  commands_total: number;
  commands_queued: number;
  commands_dispatched: number;
  commands_completed: number;
  commands_failed: number;
  device_states: number;
};

export type SensorLatestReading = {
  sensor_key: string;
  source_node: string;
  reading_time: string;
  value: number;
  unit: string;
  quality: string;
};

export type DeviceStateSummary = {
  device_key: string;
  state_payload: Record<string, unknown>;
  state_source: string;
  updated_at: string;
};

export type TimescaleStatus = {
  extension_installed: boolean;
  telemetry_is_hypertable: boolean;
};

export type SystemSummaryResponse = {
  generated_at: string;
  counts: SystemCounts;
  latest_readings: SensorLatestReading[];
  device_states: DeviceStateSummary[];
  timescale_status: TimescaleStatus;
};