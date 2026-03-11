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
  id?: number;
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

export type TelemetryHistoryPoint = {
  timestamp: string;
  value: number;
};

export type TelemetryHistorySeries = {
  sensor_key: string;
  unit: string;
  points: TelemetryHistoryPoint[];
};

export type TelemetryHistoryResponse = {
  series: TelemetryHistorySeries[];
};

export type CommandResponse = {
  id: number;
  requested_at: string;
  requested_by: string;
  target_device: string;
  command_type: string;
  command_payload: Record<string, unknown>;
  status: string;
  acknowledged_at: string | null;
  completed_at: string | null;
  error_message: string | null;
};

export type CommandListResponse = {
  items: CommandResponse[];
};

export type CommandCreateRequest = {
  requested_by: string;
  target_device: string;
  command_type: string;
  command_payload: Record<string, unknown>;
};

export type ScheduleResponse = {
  id: number;
  device_key: string;
  schedule_type: string;
  name: string;
  enabled: boolean;
  config_payload: Record<string, unknown>;
  created_at: string;
  updated_at: string;
};

export type ScheduleListResponse = {
  items: ScheduleResponse[];
};