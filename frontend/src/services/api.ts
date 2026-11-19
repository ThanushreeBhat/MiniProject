import {
  DashboardData,
  RisksResponse,
  RiskPrediction,
  TasksResponse,
  MaintenanceTask,
  ScheduleResponse,
  UnscheduledResponse,
  ExplanationsResponse,
  TaskExplanation,
  ValidationReport,
} from "../types/api";

const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL || "http://127.0.0.1:8000";

async function fetchFromApi<T>(endpoint: string): Promise<T> {
  const url = `${API_BASE_URL}${endpoint}`;
  try {
    const res = await fetch(url, {
      method: "GET",
      headers: {
        "Content-Type": "application/json",
      },
      cache: "no-store",
    });

    if (!res.ok) {
      throw new Error(`API returned HTTP ${res.status}: ${res.statusText}`);
    }

    return await res.json();
  } catch (err: unknown) {
    const message = err instanceof Error ? err.message : String(err);
    throw new Error(`Failed to fetch ${endpoint} (${message})`);
  }
}

export const api = {
  getBaseUrl: () => API_BASE_URL,

  checkHealth: async (): Promise<boolean> => {
    try {
      const res = await fetch(`${API_BASE_URL}/api/health`, {
        cache: "no-store",
      });
      return res.ok;
    } catch {
      return false;
    }
  },

  getDashboard: () => fetchFromApi<DashboardData>("/api/dashboard"),

  getRisks: () => fetchFromApi<RisksResponse>("/api/risks"),

  getRiskByAssetId: (assetId: string) =>
    fetchFromApi<RiskPrediction[]>(`/api/risks/${encodeURIComponent(assetId)}`),

  getTasks: () => fetchFromApi<TasksResponse>("/api/tasks"),

  getTaskById: (taskId: string) =>
    fetchFromApi<MaintenanceTask[]>(`/api/tasks/${encodeURIComponent(taskId)}`),

  getSchedule: () => fetchFromApi<ScheduleResponse>("/api/schedule"),

  getUnscheduled: () => fetchFromApi<UnscheduledResponse>("/api/unscheduled"),

  getExplanations: () => fetchFromApi<ExplanationsResponse>("/api/explanations"),

  getExplanationByTaskId: (taskId: string) =>
    fetchFromApi<TaskExplanation[]>(
      `/api/explanations/${encodeURIComponent(taskId)}`
    ),

  getValidation: () => fetchFromApi<ValidationReport>("/api/validation"),
};
