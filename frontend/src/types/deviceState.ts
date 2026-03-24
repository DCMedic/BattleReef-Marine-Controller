export interface DeviceStateResponse {
  id: number;
  device_key: string;
  state_payload: Record<string, unknown>;
  state_source: string;
  updated_at: string;
}