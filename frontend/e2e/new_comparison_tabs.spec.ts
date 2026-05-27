/**
 * Phase 9 E2E: tab switching on New Comparison page; Git URL input flow.
 */
import { test, expect } from "@playwright/test";
import { uniqueEmail, registerUser, loginWithToken } from "./helpers";

test.describe("New Comparison page tabs", () => {
  test.beforeEach(async ({ page, request }) => {
    const email = uniqueEmail();
    const token = await registerUser(request, email);
    await loginWithToken(page, token);
    await page.goto("/");
  });

  // Scope to the first RepositoryForm (Repo A) since both A and B share the same placeholders
  test("Local Path tab is active by default", async ({ page }) => {
    await expect(page.getByRole("heading", { name: "New Comparison" })).toBeVisible();
    await expect(page.getByPlaceholder("/path/to/codebase").first()).toBeVisible();
  });

  test("switching to Git URL tab shows URL input", async ({ page }) => {
    // Click the first "Git URL" tab (Repo A); Repo B still shows Local Path
    await page.getByTestId("tab-git").first().click();
    await expect(page.getByPlaceholder(/github\.com/i).first()).toBeVisible();
    // Repo A's git URL input is now shown; Repo B still has local path
    await expect(page.getByPlaceholder(/github\.com/i)).toHaveCount(1);
  });

  test("switching to Upload ZIP tab shows file input", async ({ page }) => {
    await page.getByTestId("tab-zip").first().click();
    await expect(page.locator('input[type="file"]').first()).toBeAttached();
  });

  test("tabs are mutually exclusive", async ({ page }) => {
    await page.getByTestId("tab-git").first().click();
    await page.getByTestId("tab-local").first().click();
    await expect(page.getByPlaceholder("/path/to/codebase").first()).toBeVisible();
    await expect(page.getByPlaceholder(/github\.com/i).first()).not.toBeVisible();
  });
});
