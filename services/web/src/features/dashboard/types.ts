export interface Measurement {
  metric: string;
  value: number;
  unit: string;
}

export interface SensorStats {
  sensor_id: string;
  device_id: string;
  kind: string;
  metrics: Array<{
    metric: string;
    unit: string;
    count: number;
    min: number;
    max: number;
    avg: number;
    last: number;
  }>;
  last_recorded_at: string | null;
}

export interface DashboardSummary {
  reading_count: number;
  sensor_count: number;
  alert_count: number;
  from_time: string | null;
  to_time: string | null;
  sensors: SensorStats[];
}

export interface TrendPoint {
  bucket_start: string | null;
  avg: number;
  min: number;
  max: number;
  count: number;
}

export interface TrendSeries {
  sensor_id: string;
  metric: string;
  unit: string;
  points: TrendPoint[];
}

export interface TrendResponse {
  interval: string;
  series: TrendSeries[];
}

export interface FarmAlert {
  id: string;
  severity: string;
  message: string;
  sensor_id: string;
  recorded_at: string | null;
}

export interface Reading {
  id: string;
  device_id: string;
  sensor_id: string;
  recorded_at: string | null;
  measurements: Measurement[];
  source: string;
}

export interface Sensor {
  sensor_id: string;
  device_id: string;
  kind: string;
  last_recorded_at: string | null;
  last_measurements: Measurement[];
}

export interface Report {
  id: string;
  title: string;
  generated_by: string;
  generated_at: string | null;
  from_time: string | null;
  to_time: string | null;
}

export interface User {
  id: string;
  username: string;
  role: string;
  is_active: boolean;
}

export interface AssistantTurn {
  role: "user" | "assistant";
  content: string;
  sources?: string[];
}

export interface AssistantReply {
  answer: string;
  sources: string[];
  model: string;
}
