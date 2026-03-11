import { apiGet, apiPost } from "./client";
import type {
  CommandCreateRequest,
  CommandListResponse,
  CommandResponse,
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

export async function createManualCommand(
  payload: CommandCreateRequest
): Promise<CommandResponse> {
  return apiPost<CommandResponse, CommandCreateRequest>("/commands", payload);
}