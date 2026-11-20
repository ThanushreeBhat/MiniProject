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
  (typeof process !== "undefined" && process.env?.NEXT_PUBLIC_API_BASE_URL) ||
  "http://127.0.0.1:8000";

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

  // 1. Dashboard
  getDashboard: () => fetchFromApi<DashboardData>("/api/dashboard"),

  // 2. Risks (all)
  getRisks: () => fetchFromApi<RisksResponse>("/api/risks"),

  // 3. Risk by Asset ID
  getRiskByAssetId: (assetId: string) =>
    fetchFromApi<RiskPrediction>(`/api/risks/${encodeURIComponent(assetId)}`),

  // 4. Tasks (all)
  getTasks: () => fetchFromApi<TasksResponse>("/api/tasks"),

  // 5. Task by Task ID
  getTaskById: (taskId: string) =>
    fetchFromApi<MaintenanceTask>(`/api/tasks/${encodeURIComponent(taskId)}`),

  // 6. Schedule (all scheduled blocks)
  getSchedule: () => fetchFromApi<ScheduleResponse>("/api/schedule"),

  // 7. Unscheduled tasks
  getUnscheduled: () => fetchFromApi<UnscheduledResponse>("/api/unscheduled"),

  // 8. Explanations (all)
  getExplanations: () => fetchFromApi<ExplanationsResponse>("/api/explanations"),

  // 9. Explanation by Task ID
  getExplanationByTaskId: (taskId: string) =>
    fetchFromApi<TaskExplanation>(
      `/api/explanations/${encodeURIComponent(taskId)}`
    ),

  // 10. Validation report
  getValidation: () => fetchFromApi<ValidationReport>("/api/validation"),
};
