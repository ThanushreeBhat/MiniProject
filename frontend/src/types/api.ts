export interface DashboardData {
  total_tasks: number;
  scheduled_tasks: number;
  unscheduled_tasks: number;
  schedule_coverage_percent: number;
  blocks_used: number;
  risk_distribution: Record<string, number>;
  validation_passed: boolean;
  total_violations: number;
}

export interface RiskPrediction {
  asset_id: string;
  predicted_failure_probability: number;
  risk_level: string;
  [key: string]: unknown;
}

export interface RisksResponse {
  total_assets: number;
  predictions: RiskPrediction[];
}

export interface MaintenanceTask {
  task_id: string;
  department: string;
  asset_type: string;
  section_id: string;
  asset_id: string;
  task_type: string;
  criticality: string;
  urgency: string;
  estimated_duration_min: number;
  earliest_start: string;
  deadline: string;
  required_resources: string;
  status: string;
  [key: string]: unknown;
}

export interface TasksResponse {
  total_tasks: number;
  tasks: MaintenanceTask[];
}

export interface ScheduledTask {
  task_id: string;
  block_window_id: string;
  section_id: string;
  scheduled_start: string;
  scheduled_end: string;
  duration_min: number;
  [key: string]: unknown;
}

export interface ScheduleResponse {
  total_scheduled: number;
  schedule: ScheduledTask[];
}

export interface UnscheduledTask {
  task_id: string;
  section_id?: string;
  reason_code?: string;
  reason?: string;
  [key: string]: unknown;
}

export interface UnscheduledResponse {
  total_unscheduled: number;
  tasks: UnscheduledTask[];
}

export interface TaskExplanation {
  task_id: string;
  status: string;
  explanation: string;
  priority_score?: number;
  [key: string]: unknown;
}

export interface ExplanationsResponse {
  total_explanations: number;
  explanations: TaskExplanation[];
}

export interface ValidationReport {
  validation_passed: boolean;
  total_violations: number;
  checks?: Record<string, boolean | string>;
  violations?: Array<Record<string, unknown>>;
  [key: string]: unknown;
}
