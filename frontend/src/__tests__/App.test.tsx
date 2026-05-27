import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { describe, expect, it, beforeEach, afterEach } from "vitest";
import App from "../App";

function wrapper({ children }: { children: React.ReactNode }) {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return (
    <QueryClientProvider client={qc}>
      <MemoryRouter>{children}</MemoryRouter>
    </QueryClientProvider>
  );
}

describe("App", () => {
  beforeEach(() => {
    // Provide a token so protected routes render (not redirected to /login)
    localStorage.setItem("access_token", "test-token");
  });

  afterEach(() => {
    localStorage.clear();
  });

  it("renders without crashing", () => {
    render(<App />, { wrapper });
    expect(document.body).toBeTruthy();
  });

  it("shows New Comparison heading on root route", () => {
    render(
      <QueryClientProvider client={new QueryClient({ defaultOptions: { queries: { retry: false } } })}>
        <MemoryRouter initialEntries={["/"]}>
          <App />
        </MemoryRouter>
      </QueryClientProvider>
    );
    expect(screen.getByRole("heading", { name: "New Comparison" })).toBeInTheDocument();
  });

  it("shows History heading on /history route", () => {
    render(
      <QueryClientProvider client={new QueryClient({ defaultOptions: { queries: { retry: false } } })}>
        <MemoryRouter initialEntries={["/history"]}>
          <App />
        </MemoryRouter>
      </QueryClientProvider>
    );
    expect(screen.getByText("Comparison History")).toBeInTheDocument();
  });
});
