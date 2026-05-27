import { render, screen, fireEvent } from "@testing-library/react";
import { describe, it, expect } from "vitest";
import FilePairTable from "../FilePairTable";
import type { FileMatch } from "../../api/comparisons";

const MATCHES: FileMatch[] = [
  {
    file_a_path: "/repo_a/src/utils.py",
    file_b_path: "/repo_b/helpers.py",
    similarity_score: 0.85,
    method_id: "line_similarity",
    detail: {},
  },
  {
    file_a_path: "/repo_a/main.py",
    file_b_path: "/repo_b/main.py",
    similarity_score: 0.40,
    method_id: "file_hash",
    detail: {},
  },
];

describe("FilePairTable", () => {
  it("shows 'No file-pair matches' when list is empty", () => {
    render(<FilePairTable matches={[]} />);
    expect(screen.getByTestId("no-matches")).toBeInTheDocument();
  });

  it("renders a row for each match", () => {
    render(<FilePairTable matches={MATCHES} />);
    const rows = screen.getAllByRole("row");
    // header + 2 data rows
    expect(rows).toHaveLength(3);
  });

  it("shows scores as percentages", () => {
    render(<FilePairTable matches={MATCHES} />);
    expect(screen.getByText("85%")).toBeInTheDocument();
    expect(screen.getByText("40%")).toBeInTheDocument();
  });

  it("sorts by score descending by default", () => {
    render(<FilePairTable matches={MATCHES} />);
    const cells = screen.getAllByText(/\d+%/);
    expect(cells[0].textContent).toBe("85%");
    expect(cells[1].textContent).toBe("40%");
  });

  it("toggles sort direction on header click (ascending)", () => {
    render(<FilePairTable matches={MATCHES} />);
    // Default is descending (85% first). One click flips to ascending (40% first).
    fireEvent.click(screen.getByText(/Score/i));
    const cells = screen.getAllByText(/\d+%/);
    expect(cells[0].textContent).toBe("40%");
  });
});
