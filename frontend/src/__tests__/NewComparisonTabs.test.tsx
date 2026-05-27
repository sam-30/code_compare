import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen, fireEvent } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { describe, it, expect, vi } from "vitest";
import NewComparisonPage from "../pages/NewComparisonPage";
import { repositoriesApi } from "../api/repositories";

vi.mock("../api/repositories");

function renderPage() {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(
    <QueryClientProvider client={qc}>
      <MemoryRouter>
        <NewComparisonPage />
      </MemoryRouter>
    </QueryClientProvider>
  );
}

describe("NewComparisonPage — tabs", () => {
  it("shows Local Path tab by default (path input visible)", () => {
    renderPage();
    expect(screen.getAllByPlaceholderText("/path/to/codebase").length).toBeGreaterThan(0);
  });

  it("switching to Git URL tab shows URL input", () => {
    renderPage();
    const gitTabs = screen.getAllByRole("tab", { name: "Git URL" });
    fireEvent.click(gitTabs[0]);
    expect(screen.getAllByPlaceholderText(/github\.com/i).length).toBeGreaterThan(0);
  });

  it("switching to Upload ZIP tab shows file input", () => {
    renderPage();
    const zipTabs = screen.getAllByRole("tab", { name: "Upload ZIP" });
    fireEvent.click(zipTabs[0]);
    // File inputs are rendered
    const fileInputs = document.querySelectorAll('input[type="file"]');
    expect(fileInputs.length).toBeGreaterThan(0);
  });

  it("switching away from Git URL hides URL input", () => {
    renderPage();
    const gitTabs = screen.getAllByRole("tab", { name: "Git URL" });
    fireEvent.click(gitTabs[0]);
    const localTabs = screen.getAllByRole("tab", { name: "Local Path" });
    fireEvent.click(localTabs[0]);
    expect(screen.queryAllByPlaceholderText(/github\.com/i)).toHaveLength(0);
  });

  it("calls create with source_type git when Git URL tab is active", async () => {
    const mockCreate = vi.fn().mockResolvedValue({
      id: 10, name: "test", path: "", source_type: "git",
      language: "python", status: "pending", file_count: 0,
      error_message: null, created_at: new Date().toISOString(), files: [],
    });
    (repositoriesApi as unknown as { create: typeof mockCreate }).create = mockCreate;

    renderPage();
    const gitTabs = screen.getAllByRole("tab", { name: "Git URL" });
    fireEvent.click(gitTabs[0]);

    const nameInputs = screen.getAllByPlaceholderText("e.g. my-project");
    const urlInputs = screen.getAllByPlaceholderText(/github\.com/i);
    fireEvent.change(nameInputs[0], { target: { value: "my-git-repo" } });
    fireEvent.change(urlInputs[0], { target: { value: "https://github.com/org/repo.git" } });

    const buttons = screen.getAllByRole("button", { name: "Register Repository" });
    fireEvent.click(buttons[0]);

    await vi.waitFor(() => {
      expect(mockCreate).toHaveBeenCalled();
      const arg = mockCreate.mock.calls[0][0];
      expect(arg.source_type).toBe("git");
      expect(arg.url).toBe("https://github.com/org/repo.git");
    });
  });
});
