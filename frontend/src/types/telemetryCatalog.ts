export interface TelemetryCatalogItem {
  sensor_key: string;
  label: string;
  unit: string;
  category: string;
  description: string;
}

export interface TelemetryCatalogResponse {
  items: TelemetryCatalogItem[];
  count: number;
}