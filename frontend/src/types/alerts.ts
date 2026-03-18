export type AlertSeverity = "info" | "warning" | "critical";

export interface RuntimeAlert {
  key: string;
  severity: AlertSeverity;
  title: string;
  message: string;
  source: string;
  metadata: Record<string, unknown>;
  active: boolean;
  created_at: string;
  updated_at: string;
}

export interface AlertsListResponse {
  generated_at: string;
  items: RuntimeAlert[];
  count: number;
  status: string;
}