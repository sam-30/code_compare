/**
 * Phase 10 E2E: login flow, redirect to login when unauthenticated.
 */
import { test, expect } from "@playwright/test";
import { uniqueEmail, registerUser } from "./helpers";

test.describe("Authentication", () => {
  test("unauthenticated visit to / redirects to /login", async ({ page }) => {
    // Navigate to a real page first so localStorage is accessible, then clear it
    await page.goto("/login");
    await page.evaluate(() => localStorage.removeItem("access_token"));

    await page.goto("/");
    await expect(page).toHaveURL(/\/login/);
    await expect(page.getByTestId("email-input")).toBeVisible();
  });

  test("register creates account and lands on app", async ({ page }) => {
    const email = uniqueEmail();
    await page.goto("/register");

    await page.getByTestId("email-input").fill(email);
    await page.getByTestId("password-input").fill("newpassword1");
    await page.getByTestId("submit-button").click();

    // Should redirect to home (New Comparison page)
    await expect(page).toHaveURL(/^http:\/\/localhost:3000\/?$/, { timeout: 10000 });
    await expect(page.getByRole("heading", { name: "New Comparison" })).toBeVisible();
  });

  test("login with valid credentials lands on app", async ({ page, request }) => {
    const email = uniqueEmail();
    await registerUser(request, email);

    await page.goto("/login");
    await page.getByTestId("email-input").fill(email);
    await page.getByTestId("password-input").fill("testpassword1");
    await page.getByTestId("submit-button").click();

    await expect(page).toHaveURL(/^http:\/\/localhost:3000\/?$/, { timeout: 10000 });
    await expect(page.getByRole("heading", { name: "New Comparison" })).toBeVisible();
  });

  test("login with wrong password shows error", async ({ page, request }) => {
    const email = uniqueEmail();
    await registerUser(request, email);

    await page.goto("/login");
    await page.getByTestId("email-input").fill(email);
    await page.getByTestId("password-input").fill("wrongpassword");
    await page.getByTestId("submit-button").click();

    await expect(page.getByTestId("error-message")).toBeVisible();
    await expect(page).toHaveURL(/\/login/);
  });

  test("sign out clears token and redirects to login", async ({ page, request }) => {
    const email = uniqueEmail();
    const token = await registerUser(request, email);

    await page.addInitScript((tok) => {
      localStorage.setItem("access_token", tok);
    }, token);
    await page.goto("/");
    await expect(page.getByRole("heading", { name: "New Comparison" })).toBeVisible();

    await page.getByTestId("logout-button").click();
    await expect(page).toHaveURL(/\/login/);
  });
});
