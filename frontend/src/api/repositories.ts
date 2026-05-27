import { api } from "./client";

export type RepositoryStatus = "pending" | "ingesting" | "ready" | "failed";

export interface RepositoryFile {
  id: number;
  relative_path: string;
  sha256: string;
  size_bytes: number;
  line_count: number;
}

export interface Repository {
  id: number;
  name: string;
  path: string;
  source_type: string;
  language: string;
  status: RepositoryStatus;
  file_count: number;
  error_message: string | null;
  created_at: string;
  files: RepositoryFile[];
}

export interface RepositoryListItem {
  id: number;
  name: string;
  language: string;
  status: RepositoryStatus;
  file_count: number;
  created_at: string;
}

export interface CreateRepositoryPayload {
  name: string;
  path?: string;
  language: string;
  source_type?: "local" | "git";
  url?: string;
}

export const repositoriesApi = {
  create: (payload: CreateRepositoryPayload) =>
    api.post<Repository>("/repos", payload).then((r) => r.data),

  upload: (name: string, language: string, file: File) => {
    const form = new FormData();
    form.append("name", name);
    form.append("language", language);
    form.append("file", file);
    return api.post<Repository>("/repos/upload", form, {
      headers: { "Content-Type": "multipart/form-data" },
    }).then((r) => r.data);
  },

  list: () =>
    api.get<RepositoryListItem[]>("/repos").then((r) => r.data),

  get: (id: number) =>
    api.get<Repository>(`/repos/${id}`).then((r) => r.data),

  delete: (id: number) =>
    api.delete(`/repos/${id}`),
};
