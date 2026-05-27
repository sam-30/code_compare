import { render, screen } from "@testing-library/react";
import { describe, it, expect } from "vitest";
import ScoreGauge from "../ScoreGauge";

describe("ScoreGauge", () => {
  it("shows 'Calculating…' when score is null", () => {
    render(<ScoreGauge score={null} />);
    expect(screen.getByText("Calculating…")).toBeInTheDocument();
  });

  it("renders the correct percentage for a score", () => {
    render(<ScoreGauge score={0.75} />);
    expect(screen.getByTestId("score-pct").textContent).toBe("75%");
  });

  it("shows Low Similarity label for score < 0.3", () => {
    render(<ScoreGauge score={0.1} />);
    expect(screen.getByTestId("score-label").textContent).toBe("Low Similarity");
  });

  it("shows Moderate Similarity label for 0.3 <= score < 0.7", () => {
    render(<ScoreGauge score={0.5} />);
    expect(screen.getByTestId("score-label").textContent).toBe("Moderate Similarity");
  });

  it("shows High Similarity label for score >= 0.7", () => {
    render(<ScoreGauge score={0.9} />);
    expect(screen.getByTestId("score-label").textContent).toBe("High Similarity");
  });

  it("renders the gauge container", () => {
    render(<ScoreGauge score={0.5} />);
    expect(screen.getByTestId("score-gauge")).toBeInTheDocument();
  });
});
