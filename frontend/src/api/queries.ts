import { apiGet } from "./client";
import type { SystemSummaryResponse } from "../types";

export async function fetchSystemSummary(): Promise<SystemSummaryResponse> {
  return apiGet<SystemSummaryResponse>("/system/summary");
}