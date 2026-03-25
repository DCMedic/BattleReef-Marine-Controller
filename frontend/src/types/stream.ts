import type { RuntimeAlert } from "./alerts";
import type { DeviceStateResponse } from "./deviceState";
import type { CommandResponse, SystemSummaryResponse } from "./index";

export interface StreamSnapshot {
  timestamp: string;
  summary: SystemSummaryResponse;
  commands: CommandResponse[];
  device_states: DeviceStateResponse[];
  alerts: RuntimeAlert[];
}

export interface StreamErrorPayload {
  timestamp: string;
  error: string;
}