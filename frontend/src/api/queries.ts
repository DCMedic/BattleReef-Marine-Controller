import { apiGet } from "./client";
import type { SystemSummaryResponse, TelemetryHistoryResponse } from "../types";

export async function fetchSystemSummary(): Promise<SystemSummaryResponse> {
  return apiGet<SystemSummaryResponse>("/system/summary");
}

export async function fetchTelemetryHistory(): Promise<TelemetryHistoryResponse> {
  return apiGet<TelemetryHistoryResponse>(
    "/telemetry/history?sensor_keys=tank_temp_main,tank_ph_main,tank_salinity_main,sump_level_main&limit=120"
  );
}