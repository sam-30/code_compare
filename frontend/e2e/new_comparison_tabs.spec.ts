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

  // Default tab is now Git URL (most common use case)
  test("Git URL tab is active by default", async ({ page }) => {
    await expect(page.getByRole("heading", { name: "New Comparison" })).toBeVisible();
    await expect(page.getByPlaceholder(/github\.com/i).first()).toBeVisible();
  });

  test("switching to Local Path tab shows path input", async ({ page }) => {
    // Click the first "Local Path" tab (Repo A); Repo B still shows Git URL
    await page.getByTestId("tab-local").first().click();
    await expect(page.getByPlaceholder("/path/to/codebase").first()).toBeVisible();
    // Repo A switched to local; Repo B still on git URL
    await expect(page.getByPlaceholder(/github\.com/i)).toHaveCount(1);
  });

  test("switching to Upload ZIP tab shows file input", async ({ page }) => {
    await page.getByTestId("tab-zip").first().click();
    await expect(page.locator('input[type="file"]').first()).toBeAttached();
  });

  test("tabs are mutually exclusive", async ({ page }) => {
    // Switch Repo A to local, then back to git — local input should disappear
    await page.getByTestId("tab-local").first().click();
    await expect(page.getByPlaceholder("/path/to/codebase").first()).toBeVisible();
    await page.getByTestId("tab-git").first().click();
    await expect(page.getByPlaceholder(/github\.com/i).first()).toBeVisible();
    await expect(page.getByPlaceholder("/path/to/codebase").first()).not.toBeVisible();
  });
});
