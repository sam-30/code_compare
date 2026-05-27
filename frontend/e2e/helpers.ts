import { execSync } from "child_process";
import { APIRequestContext, Page } from "@playwright/test";

export const API = "http://localhost:3000/api";
const BACKEND_CONTAINER = "code_comparison-backend-1";

let _emailCounter = 0;

export function uniqueEmail() {
  return `e2e_user_${Date.now()}_${++_emailCounter}@example.com`;
}

/** Register a fresh user and return the token. */
export async function registerUser(
  request: APIRequestContext,
  email: string,
  password = "testpassword1"
): Promise<string> {
  const resp = await request.post(`${API}/auth/register`, {
    data: { email, password },
  });
  if (!resp.ok()) {
    throw new Error(`Register failed: ${resp.status()} ${await resp.text()}`);
  }
  const body = await resp.json();
  return body.access_token;
}

/** Set auth token in localStorage before the first page.goto(). */
export async function loginWithToken(page: Page, token: string) {
  await page.addInitScript((tok) => {
    localStorage.setItem("access_token", tok);
  }, token);
}

/**
 * Create a temporary directory with a Python file inside the Docker backend
 * container (needed because the backend validates paths on its own filesystem).
 * Returns the container-internal path.
 */
export function makeContainerRepo(suffix: string, code = "def foo(): return 1\n"): string {
  const dir = `/tmp/e2e_${suffix}_${Date.now()}`;
  execSync(`docker exec ${BACKEND_CONTAINER} mkdir -p ${dir}`);
  execSync(`docker exec ${BACKEND_CONTAINER} sh -c 'echo "${code}" > ${dir}/main.py'`);
  return dir;
}

/** Wait for a repo/comparison to reach a terminal status via polling. */
export async function waitForStatus(
  request: APIRequestContext,
  url: string,
  token: string,
  terminal: string[],
  maxMs = 15000
): Promise<Record<string, unknown>> {
  const deadline = Date.now() + maxMs;
  while (Date.now() < deadline) {
    await new Promise((r) => setTimeout(r, 500));
    const r = await request.get(`${API}${url}`, {
      headers: { Authorization: `Bearer ${token}` },
    });
    const body = await r.json() as Record<string, unknown>;
    if (terminal.includes(body.status as string)) return body;
  }
  throw new Error(`Timed out waiting for ${url} to reach ${terminal.join("|")}`);
}
