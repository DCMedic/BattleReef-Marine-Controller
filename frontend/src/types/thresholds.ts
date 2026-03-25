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
  active_profile: string | null;
}

export interface ThresholdUpdateRequest {
  min: number | null;
  max: number | null;
  severity: "warning" | "critical";
  enabled: boolean;
}

export interface ThresholdPresetItem {
  key: string;
  label: string;
  description: string;
  active: boolean;
  threshold_count: number;
}

export interface ThresholdPresetListResponse {
  items: ThresholdPresetItem[];
  count: number;
  active_profile: string | null;
}