import { api } from "./client";

export interface TokenOut {
  access_token: string;
  token_type: string;
}

export interface UserOut {
  id: number;
  email: string;
  created_at: string;
}

export const authApi = {
  register: (email: string, password: string) =>
    api.post<TokenOut>("/auth/register", { email, password }).then((r) => r.data),

  login: (email: string, password: string) =>
    api.post<TokenOut>("/auth/login", { email, password }).then((r) => r.data),

  me: () =>
    api.get<UserOut>("/auth/me").then((r) => r.data),
};

const TOKEN_KEY = "access_token";

export const tokenStorage = {
  get: (): string | null => localStorage.getItem(TOKEN_KEY),
  set: (token: string) => localStorage.setItem(TOKEN_KEY, token),
  clear: () => localStorage.removeItem(TOKEN_KEY),
};
