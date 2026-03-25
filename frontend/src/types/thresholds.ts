export interface ThresholdConfigItem {
  sensor_key: string;
  label: string;
  unit: string | null;
  severity: "warning" | "critical";
  min: number | null;
  max: number | null;
  enabled: boolean;
  has_override: boolean;
  default: Record<string, unknown>;
  effective: Record<string, unknown>;
}

export interface ThresholdListResponse {
  items: ThresholdConfigItem[];
  count: number;
}

export interface ThresholdUpdateRequest {
  min: number | null;
  max: number | null;
  severity: "warning" | "critical";
  enabled: boolean;
}