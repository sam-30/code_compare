import { render, screen, fireEvent } from "@testing-library/react";
import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import ExportButton from "../ExportButton";

describe("ExportButton", () => {
  let clickSpy: ReturnType<typeof vi.fn>;
  let originalCreateElement: typeof document.createElement;

  beforeEach(() => {
    clickSpy = vi.fn();
    originalCreateElement = document.createElement.bind(document);
    vi.spyOn(document, "createElement").mockImplementation((tag: string) => {
      const el = originalCreateElement(tag);
      if (tag === "a") {
        Object.defineProperty(el, "click", { value: clickSpy, configurable: true });
      }
      return el;
    });
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("renders JSON and PDF export buttons", () => {
    render(<ExportButton comparisonId={5} />);
    expect(screen.getByRole("button", { name: "Export JSON" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Export PDF" })).toBeInTheDocument();
  });

  it("triggers download on JSON button click", () => {
    render(<ExportButton comparisonId={5} />);
    fireEvent.click(screen.getByRole("button", { name: "Export JSON" }));
    expect(clickSpy).toHaveBeenCalledOnce();
  });

  it("triggers download on PDF button click", () => {
    render(<ExportButton comparisonId={5} />);
    fireEvent.click(screen.getByRole("button", { name: "Export PDF" }));
    expect(clickSpy).toHaveBeenCalledOnce();
  });
});
