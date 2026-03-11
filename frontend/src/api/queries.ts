import { apiGet, apiPost, apiPostEmpty } from "./client";
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

export async function fetchSystemSummary(): Promise<SystemSummaryResponse> {
  return apiGet<SystemSummaryResponse>("/system/summary");
}

export async function fetchTelemetryHistory(): Promise<TelemetryHistoryResponse> {
  return apiGet<TelemetryHistoryResponse>(
    "/telemetry/history?sensor_keys=tank_temp_main,tank_ph_main,tank_salinity_main,sump_level_main&limit=120"
  );
}

export async function fetchRecentCommands(): Promise<CommandListResponse> {
  return apiGet<CommandListResponse>("/commands?limit=10");
}

export async function fetchSchedules(): Promise<ScheduleListResponse> {
  return apiGet<ScheduleListResponse>("/schedules?limit=100");
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
  return apiPost<ScheduleResponse, ScheduleUpdateRequest>(
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

export async function evaluateScheduleRules(): Promise<{
  evaluated_at: string;
  schedule_hour_utc: number;
  results: Array<Record<string, unknown>>;
}> {
  return apiPostEmpty("/commands/evaluate/schedule");
}