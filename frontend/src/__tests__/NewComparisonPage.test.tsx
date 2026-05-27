import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { describe, expect, it, vi, beforeEach } from "vitest";
import NewComparisonPage from "../pages/NewComparisonPage";
import { repositoriesApi } from "../api/repositories";

vi.mock("../api/repositories");

const mockedApi = repositoriesApi as unknown as {
  create: ReturnType<typeof vi.fn>;
  list: ReturnType<typeof vi.fn>;
  get: ReturnType<typeof vi.fn>;
  delete: ReturnType<typeof vi.fn>;
};

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

describe("NewComparisonPage", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("renders two repository forms", () => {
    renderPage();
    expect(screen.getByText("Reference Repository (Repo A)")).toBeInTheDocument();
    expect(screen.getByText("Suspect Repository (Repo B)")).toBeInTheDocument();
  });

  it("shows language selector with Python and JavaScript options", () => {
    renderPage();
    const selects = screen.getAllByRole("combobox");
    expect(selects.length).toBe(2);
  });

  it("calls API and shows status on submit", async () => {
    mockedApi.create = vi.fn().mockResolvedValue({
      id: 1,
      name: "test-repo",
      path: "/tmp/test",
      source_type: "local",
      language: "python",
      status: "ingesting",
      file_count: 0,
      error_message: null,
      created_at: new Date().toISOString(),
      files: [],
    });
    mockedApi.get = vi.fn().mockResolvedValue({
      id: 1,
      name: "test-repo",
      path: "/tmp/test",
      source_type: "local",
      language: "python",
      status: "ready",
      file_count: 5,
      error_message: null,
      created_at: new Date().toISOString(),
      files: [],
    });

    renderPage();
    const nameInputs = screen.getAllByPlaceholderText("e.g. my-project");
    const pathInputs = screen.getAllByPlaceholderText("/path/to/codebase");
    const buttons = screen.getAllByRole("button", { name: "Register Repository" });

    fireEvent.change(nameInputs[0], { target: { value: "test-repo" } });
    fireEvent.change(pathInputs[0], { target: { value: "/tmp/test" } });
    fireEvent.click(buttons[0]);

    await waitFor(() => {
      expect(mockedApi.create).toHaveBeenCalled();
      const firstArg = mockedApi.create.mock.calls[0][0];
      expect(firstArg).toEqual({ name: "test-repo", path: "/tmp/test", language: "python" });
    });
  });
});
