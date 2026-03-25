import { apiDelete, apiGet, apiPost, apiPostEmpty, apiPut } from "./client";
import type {
  CommandCreateRequest,
  CommandListResponse,
  CommandResponse,
  DeviceStateSummary,
  ScheduleCreateRequest,
  ScheduleListResponse,
  ScheduleResponse,
  ScheduleUpdateRequest,
  SystemSummaryResponse,
  TelemetryHistoryResponse,
} from "../types";
import type { AlertsListResponse } from "../types/alerts";
import type { DeviceStateResponse } from "../types/deviceState";
import type {
  ThresholdConfigItem,
  ThresholdListResponse,
  ThresholdPresetListResponse,
  ThresholdUpdateRequest,
} from "../types/thresholds";
import type { TelemetryCatalogResponse } from "../types/telemetryCatalog";
import type { TelemetryWindowResponse } from "../types/telemetryTrends";

const DEFAULT_HISTORY_SENSOR_KEYS = [
  "tank_temp_main",
  "tank_ph_main",
  "tank_salinity_main",
  "sump_level_main",
  "orp_main",
  "dissolved_oxygen_main",
  "flow_return_main",
  "flow_manifold_main",
  "par_left",
  "par_center",
  "par_right",
  "leak_probe_a",
  "leak_probe_b",
  "room_co2_main",
  "power_monitor_main",
  "voc_main",
  "ambient_temp_room",
  "ambient_humidity_room",
];

export async function fetchSystemSummary(): Promise<SystemSummaryResponse> {
  return apiGet<SystemSummaryResponse>("/system/summary");
}

export async function fetchTelemetryCatalog(): Promise<TelemetryCatalogResponse> {
  return apiGet<TelemetryCatalogResponse>("/telemetry/catalog");
}

export async function fetchTelemetryHistory(
  sensorKeys: string[] = DEFAULT_HISTORY_SENSOR_KEYS,
  limit = 120
): Promise<TelemetryHistoryResponse> {
  const params = new URLSearchParams({
    sensor_keys: sensorKeys.join(","),
    limit: String(limit),
  });

  return apiGet<TelemetryHistoryResponse>(`/telemetry/history?${params.toString()}`);
}

export async function fetchRecentCommands(limit = 10): Promise<CommandListResponse> {
  return apiGet<CommandListResponse>(`/commands?limit=${limit}`);
}

export async function fetchSchedules(limit = 100): Promise<ScheduleListResponse> {
  return apiGet<ScheduleListResponse>(`/schedules?limit=${limit}`);
}

export async function seedDefaultSchedules(): Promise<ScheduleListResponse> {
  return apiPostEmpty<ScheduleListResponse>("/schedules/seed-defaults");
}

export async function createSchedule(
  payload: ScheduleCreateRequest
): Promise<ScheduleResponse> {
  return apiPost<ScheduleResponse, ScheduleCreateRequest>("/schedules", payload);
}

export async function updateSchedule(
  scheduleId: number,
  payload: ScheduleUpdateRequest
): Promise<ScheduleResponse> {
  return apiPut<ScheduleResponse, ScheduleUpdateRequest>(
    `/schedules/${scheduleId}`,
    payload
  );
}

export async function createManualCommand(
  payload: CommandCreateRequest
): Promise<CommandResponse> {
  return apiPost<CommandResponse, CommandCreateRequest>("/commands", payload);
}

export async function setDeviceMode(
  deviceKey: string,
  mode: "auto" | "manual"
): Promise<DeviceStateSummary> {
  return apiPostEmpty<DeviceStateSummary>(`/device-states/${deviceKey}/mode/${mode}`);
}

export async function fetchDeviceState(deviceKey: string): Promise<DeviceStateResponse> {
  return apiGet<DeviceStateResponse>(`/device-states/${deviceKey}`);
}

export async function evaluateScheduleRules(): Promise<{
  evaluated_at: string;
  schedule_hour_utc: number;
  results: Array<Record<string, unknown>>;
}> {
  return apiPostEmpty("/commands/evaluate/schedule");
}

export async function fetchAlerts(): Promise<AlertsListResponse> {
  return apiGet<AlertsListResponse>("/alerts");
}

export async function clearAlert(alertKey: string): Promise<{ status: string; cleared: string }> {
  return apiDelete<{ status: string; cleared: string }>(`/alerts/${alertKey}`);
}

export async function clearAllAlerts(): Promise<{ status: string; cleared_count: number }> {
  return apiDelete<{ status: string; cleared_count: number }>("/alerts");
}

export async function fetchThresholds(): Promise<ThresholdListResponse> {
  return apiGet<ThresholdListResponse>("/thresholds");
}

export async function fetchThresholdPresets(): Promise<ThresholdPresetListResponse> {
  return apiGet<ThresholdPresetListResponse>("/thresholds/presets");
}

export async function applyThresholdPreset(
  presetKey: string
): Promise<{
  applied_profile: string;
  label: string;
  description: string;
  threshold_count: number;
}> {
  return apiPost("/thresholds/presets/apply", { preset_key: presetKey });
}

export async function clearActiveThresholdPreset(): Promise<{ active_profile: null }> {
  return apiDelete<{ active_profile: null }>("/thresholds/presets/active");
}

export async function updateThreshold(
  sensorKey: string,
  payload: ThresholdUpdateRequest
): Promise<ThresholdConfigItem> {
  return apiPut<ThresholdConfigItem, ThresholdUpdateRequest>(`/thresholds/${sensorKey}`, payload);
}

export async function resetThreshold(sensorKey: string): Promise<ThresholdConfigItem> {
  return apiDelete<ThresholdConfigItem>(`/thresholds/${sensorKey}`);
}

export async function fetchTelemetryWindow(
  sensorKey: string,
  days = 3,
  maxPoints = 288
): Promise<TelemetryWindowResponse> {
  const params = new URLSearchParams({
    sensor_key: sensorKey,
    days: String(days),
    max_points: String(maxPoints),
  });

  return apiGet<TelemetryWindowResponse>(`/telemetry/window?${params.toString()}`);
}