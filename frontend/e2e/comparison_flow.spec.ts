/**
 * Phase 6+7 E2E: full comparison flow — register repos → run comparison →
 * results page shows score gauge, method breakdown, and file-pair table.
 */
import { test, expect } from "@playwright/test";
import {
  API, uniqueEmail, registerUser, loginWithToken,
  makeContainerRepo, waitForStatus,
} from "./helpers";

test.describe("Full comparison flow", () => {
  test("ingest two repos, run comparison, see results", async ({ page, request }) => {
    const email = uniqueEmail();
    const token = await registerUser(request, email);
    await loginWithToken(page, token);

    const code = "def alpha(): return 1\ndef beta(): return 2\n";
    const dirA = makeContainerRepo("a", code);
    const dirB = makeContainerRepo("b", code);

    const repoA = await request.post(`${API}/repos`, {
      data: { name: "RepoA", path: dirA, language: "python" },
      headers: { Authorization: `Bearer ${token}` },
    });
    expect(repoA.ok()).toBeTruthy();
    const repoAId = (await repoA.json()).id as number;

    const repoB = await request.post(`${API}/repos`, {
      data: { name: "RepoB", path: dirB, language: "python" },
      headers: { Authorization: `Bearer ${token}` },
    });
    expect(repoB.ok()).toBeTruthy();
    const repoBId = (await repoB.json()).id as number;

    // Wait for both repos to finish ingesting
    await waitForStatus(request, `/repos/${repoAId}`, token, ["ready", "failed"]);
    await waitForStatus(request, `/repos/${repoBId}`, token, ["ready", "failed"]);

    // Create comparison using only fast methods
    const cmp = await request.post(`${API}/comparisons`, {
      data: {
        repo_a_id: repoAId,
        repo_b_id: repoBId,
        language: "python",
        config: {
          enabled_methods: ["file_hash", "function_names"],
          method_weights: { file_hash: 0.5, function_names: 0.5 },
        },
      },
      headers: { Authorization: `Bearer ${token}` },
    });
    expect(cmp.ok()).toBeTruthy();
    const cmpId = (await cmp.json()).id as number;

    // Wait for comparison to complete
    await waitForStatus(request, `/comparisons/${cmpId}`, token, ["complete", "failed"]);

    // Navigate to results page
    await page.goto(`/comparisons/${cmpId}`);
    await page.waitForTimeout(3000); // let SSE events arrive
    await page.screenshot({ path: "test-results/debug-results-page.png", fullPage: true });

    // Score gauge should be visible
    await expect(page.getByTestId("score-pct")).toBeVisible({ timeout: 15000 });

    // Method breakdown rows should exist
    await expect(page.getByTestId("method-row-file_hash")).toBeVisible();
    await expect(page.getByTestId("method-row-function_names")).toBeVisible();
  });

  test("History page shows past comparisons", async ({ page, request }) => {
    const email = uniqueEmail();
    const token = await registerUser(request, email);
    await loginWithToken(page, token);

    const dirA = makeContainerRepo("ha");
    const dirB = makeContainerRepo("hb");

    const rA = await request.post(`${API}/repos`, {
      data: { name: "HistA", path: dirA, language: "python" },
      headers: { Authorization: `Bearer ${token}` },
    });
    const rB = await request.post(`${API}/repos`, {
      data: { name: "HistB", path: dirB, language: "python" },
      headers: { Authorization: `Bearer ${token}` },
    });
    const rAId = (await rA.json()).id as number;
    const rBId = (await rB.json()).id as number;

    await waitForStatus(request, `/repos/${rAId}`, token, ["ready", "failed"]);
    await waitForStatus(request, `/repos/${rBId}`, token, ["ready", "failed"]);

    const cmpResp = await request.post(`${API}/comparisons`, {
      data: {
        repo_a_id: rAId, repo_b_id: rBId, language: "python",
        config: { enabled_methods: ["file_hash"], method_weights: { file_hash: 1.0 } },
      },
      headers: { Authorization: `Bearer ${token}` },
    });
    const cmpId = (await cmpResp.json()).id as number;
    await waitForStatus(request, `/comparisons/${cmpId}`, token, ["complete", "failed"]);

    await page.goto("/history");
    await expect(page.getByText("Comparison History")).toBeVisible();
    // The comparison should appear in the list
    await expect(page.locator(`text=#${cmpId}`)).toBeVisible({ timeout: 5000 });
  });
});
