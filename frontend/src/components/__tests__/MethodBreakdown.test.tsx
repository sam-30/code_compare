import { render, screen } from "@testing-library/react";
import { describe, it, expect } from "vitest";
import MethodBreakdown from "../MethodBreakdown";
import type { MethodResult } from "../../api/comparisons";

const METHODS: MethodResult[] = [
  { method_id: "file_hash", score: 0.9, weight: 0.15, details: {}, duration_ms: 10 },
  { method_id: "line_similarity", score: 0.5, weight: 0.20, details: {}, duration_ms: 20 },
  { method_id: "function_names", score: 0.2, weight: 0.15, details: {}, duration_ms: 5 },
];

describe("MethodBreakdown", () => {
  it("renders a row for each method", () => {
    render(<MethodBreakdown methods={METHODS} />);
    expect(screen.getByTestId("method-row-file_hash")).toBeInTheDocument();
    expect(screen.getByTestId("method-row-line_similarity")).toBeInTheDocument();
    expect(screen.getByTestId("method-row-function_names")).toBeInTheDocument();
  });

  it("displays score as percentage", () => {
    render(<MethodBreakdown methods={METHODS} />);
    expect(screen.getByTestId("score-file_hash").textContent).toBe("90%");
    expect(screen.getByTestId("score-line_similarity").textContent).toBe("50%");
    expect(screen.getByTestId("score-function_names").textContent).toBe("20%");
  });

  it("renders the outer breakdown container", () => {
    render(<MethodBreakdown methods={METHODS} />);
    expect(screen.getByTestId("method-breakdown")).toBeInTheDocument();
  });

  it("shows human-readable method labels", () => {
    render(<MethodBreakdown methods={METHODS} />);
    expect(screen.getByText("File Hash")).toBeInTheDocument();
    expect(screen.getByText("Line Similarity")).toBeInTheDocument();
  });
});
