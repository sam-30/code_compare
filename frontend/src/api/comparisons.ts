import { api } from "./client";

export type ComparisonStatus = "pending" | "running" | "complete" | "failed";

export interface MethodResult {
  method_id: string;
  score: number;
  weight: number;
  details: Record<string, unknown>;
  duration_ms: number;
}

export interface FileMatch {
  file_a_path: string;
  file_b_path: string;
  similarity_score: number;
  method_id: string;
  detail: Record<string, unknown>;
}

export interface ComparisonDetail {
  id: number;
  repo_a_id: number;
  repo_b_id: number;
  language: string;
  status: ComparisonStatus;
  overall_score: number | null;
  config: Record<string, unknown>;
  error_message: string | null;
  created_at: string;
  completed_at: string | null;
  method_results: MethodResult[];
  file_matches: FileMatch[];
}

export interface ComparisonListItem {
  id: number;
  repo_a_id: number;
  repo_b_id: number;
  language: string;
  status: ComparisonStatus;
  overall_score: number | null;
  created_at: string;
  completed_at: string | null;
}

export const comparisonsApi = {
  list: async (): Promise<ComparisonListItem[]> => {
    const res = await api.get<ComparisonListItem[]>("/comparisons");
    return res.data;
  },
  get: async (id: number): Promise<ComparisonDetail> => {
    const res = await api.get<ComparisonDetail>(`/comparisons/${id}`);
    return res.data;
  },
  create: async (payload: {
    repo_a_id: number;
    repo_b_id: number;
    language: string;
    config?: Record<string, unknown>;
    config_id?: number;
  }): Promise<ComparisonDetail> => {
    const res = await api.post<ComparisonDetail>("/comparisons", payload);
    return res.data;
  },
  delete: async (id: number): Promise<void> => {
    await api.delete(`/comparisons/${id}`);
  },
};
