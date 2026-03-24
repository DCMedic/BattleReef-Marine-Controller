import type { DeviceStateResponse } from "./deviceState";
import type { CommandResponse, SystemSummaryResponse } from "./index";

export interface StreamSnapshot {
  timestamp: string;
  summary: SystemSummaryResponse;
  commands: CommandResponse[];
  device_states: DeviceStateResponse[];
}

export interface StreamErrorPayload {
  timestamp: string;
  error: string;
}