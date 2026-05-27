import { api } from "./client";

export interface ComparisonConfig {
  id: number;
  name: string;
  description: string;
  method_weights: Record<string, number>;
  is_default: boolean;
}

export interface CreateConfigPayload {
  name: string;
  description?: string;
  method_weights: Record<string, number>;
  is_default?: boolean;
}

export interface UpdateConfigPayload {
  name?: string;
  description?: string;
  method_weights?: Record<string, number>;
  is_default?: boolean;
}

export const configsApi = {
  list: async (): Promise<ComparisonConfig[]> => {
    const res = await api.get<ComparisonConfig[]>("/configs");
    return res.data;
  },
  get: async (id: number): Promise<ComparisonConfig> => {
    const res = await api.get<ComparisonConfig>(`/configs/${id}`);
    return res.data;
  },
  create: async (payload: CreateConfigPayload): Promise<ComparisonConfig> => {
    const res = await api.post<ComparisonConfig>("/configs", payload);
    return res.data;
  },
  update: async (id: number, payload: UpdateConfigPayload): Promise<ComparisonConfig> => {
    const res = await api.put<ComparisonConfig>(`/configs/${id}`, payload);
    return res.data;
  },
  delete: async (id: number): Promise<void> => {
    await api.delete(`/configs/${id}`);
  },
};
