import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import ConfigEditor from "../ConfigEditor";
import { configsApi } from "../../api/configs";

vi.mock("../../api/configs");

const mockedApi = configsApi as unknown as {
  create: ReturnType<typeof vi.fn>;
};

function renderEditor(onSaved = vi.fn()) {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(
    <QueryClientProvider client={qc}>
      <ConfigEditor onSaved={onSaved} />
    </QueryClientProvider>
  );
}

describe("ConfigEditor", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("renders all 9 method rows", () => {
    renderEditor();
    const methodIds = [
      "file_hash", "line_similarity", "function_names", "ast_structure",
      "token_ngram", "call_graph", "import_analysis", "identifier_similarity",
      "complexity_profile",
    ];
    methodIds.forEach((id) => {
      expect(screen.getByTestId(`method-row-${id}`)).toBeInTheDocument();
    });
    expect(screen.getAllByRole("checkbox")).toHaveLength(9);
  });

  it("save button is disabled when name is empty", () => {
    renderEditor();
    expect(screen.getByRole("button", { name: "Save Preset" })).toBeDisabled();
  });

  it("save button is enabled after name is typed", () => {
    renderEditor();
    fireEvent.change(screen.getByLabelText(/Preset Name/i), {
      target: { value: "My Preset" },
    });
    expect(screen.getByRole("button", { name: "Save Preset" })).not.toBeDisabled();
  });

  it("calls configsApi.create with name and method_weights on save", async () => {
    mockedApi.create = vi.fn().mockResolvedValue({
      id: 1,
      name: "My Preset",
      description: "",
      method_weights: { file_hash: 1 },
      is_default: false,
    });

    renderEditor();
    fireEvent.change(screen.getByLabelText(/Preset Name/i), {
      target: { value: "My Preset" },
    });
    fireEvent.click(screen.getByRole("button", { name: "Save Preset" }));

    await waitFor(() => {
      expect(mockedApi.create).toHaveBeenCalledOnce();
      const arg = mockedApi.create.mock.calls[0][0];
      expect(arg.name).toBe("My Preset");
      expect(typeof arg.method_weights).toBe("object");
      expect(Object.keys(arg.method_weights).length).toBeGreaterThan(0);
    });
  });

  it("disabling a method removes it from the submit payload", async () => {
    mockedApi.create = vi.fn().mockResolvedValue({
      id: 2,
      name: "No Hash",
      description: "",
      method_weights: {},
      is_default: false,
    });

    renderEditor();
    // First checkbox = "Enable Exact File Hash"
    const checkboxes = screen.getAllByRole("checkbox");
    fireEvent.click(checkboxes[0]); // toggle off file_hash

    fireEvent.change(screen.getByLabelText(/Preset Name/i), {
      target: { value: "No Hash" },
    });
    fireEvent.click(screen.getByRole("button", { name: "Save Preset" }));

    await waitFor(() => {
      expect(mockedApi.create).toHaveBeenCalledOnce();
      const arg = mockedApi.create.mock.calls[0][0];
      expect("file_hash" in arg.method_weights).toBe(false);
    });
  });

  it("disabling all methods disables the save button", () => {
    renderEditor();
    // Toggle off all 9
    screen.getAllByRole("checkbox").forEach((cb) => fireEvent.click(cb));
    fireEvent.change(screen.getByLabelText(/Preset Name/i), {
      target: { value: "Empty" },
    });
    expect(screen.getByRole("button", { name: "Save Preset" })).toBeDisabled();
  });

  it("calls onSaved with the new config id", async () => {
    mockedApi.create = vi.fn().mockResolvedValue({
      id: 42,
      name: "CB Test",
      description: "",
      method_weights: { file_hash: 1 },
      is_default: false,
    });

    const onSaved = vi.fn();
    renderEditor(onSaved);
    fireEvent.change(screen.getByLabelText(/Preset Name/i), {
      target: { value: "CB Test" },
    });
    fireEvent.click(screen.getByRole("button", { name: "Save Preset" }));

    await waitFor(() => {
      expect(onSaved).toHaveBeenCalledWith(42);
    });
  });
});
