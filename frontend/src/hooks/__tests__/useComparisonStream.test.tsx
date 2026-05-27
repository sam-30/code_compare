import { renderHook, act } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { useComparisonStream } from "../useComparisonStream";

// Minimal EventSource mock
class MockEventSource {
  onmessage: ((event: MessageEvent) => void) | null = null;
  onerror: (() => void) | null = null;
  closed = false;

  constructor(public url: string) {}

  close() {
    this.closed = true;
  }

  emit(data: object) {
    const event = new MessageEvent("message", { data: JSON.stringify(data) });
    this.onmessage?.(event);
  }

  triggerError() {
    this.onerror?.();
  }
}

let mockEsInstance: MockEventSource | null = null;

beforeEach(() => {
  mockEsInstance = null;
  vi.stubGlobal(
    "EventSource",
    vi.fn((url: string) => {
      mockEsInstance = new MockEventSource(url);
      return mockEsInstance;
    })
  );
});

describe("useComparisonStream", () => {
  it("starts with pending status and empty methods", () => {
    const { result } = renderHook(() => useComparisonStream(1));
    expect(result.current.status).toBe("pending");
    expect(result.current.methods).toHaveLength(0);
    expect(result.current.streamDone).toBe(false);
  });

  it("accumulates method events", () => {
    const { result } = renderHook(() => useComparisonStream(1));
    act(() => {
      mockEsInstance!.emit({
        type: "method", method_id: "file_hash", score: 0.9, weight: 0.15, details: {}, duration_ms: 5,
      });
    });
    expect(result.current.methods).toHaveLength(1);
    expect(result.current.methods[0].method_id).toBe("file_hash");
    expect(result.current.status).toBe("running");
  });

  it("does not duplicate method entries", () => {
    const { result } = renderHook(() => useComparisonStream(1));
    act(() => {
      mockEsInstance!.emit({
        type: "method", method_id: "file_hash", score: 0.9, weight: 0.15, details: {}, duration_ms: 5,
      });
      mockEsInstance!.emit({
        type: "method", method_id: "file_hash", score: 0.9, weight: 0.15, details: {}, duration_ms: 5,
      });
    });
    expect(result.current.methods).toHaveLength(1);
  });

  it("sets done and overall score on 'done' event", () => {
    const { result } = renderHook(() => useComparisonStream(1));
    act(() => {
      mockEsInstance!.emit({ type: "done", overall_score: 0.72 });
    });
    expect(result.current.status).toBe("complete");
    expect(result.current.overallScore).toBe(0.72);
    expect(result.current.streamDone).toBe(true);
  });

  it("sets failed status on 'error' event", () => {
    const { result } = renderHook(() => useComparisonStream(1));
    act(() => {
      mockEsInstance!.emit({ type: "error", message: "something went wrong" });
    });
    expect(result.current.status).toBe("failed");
    expect(result.current.streamDone).toBe(true);
  });

  it("sets streamDone on EventSource onerror", () => {
    const { result } = renderHook(() => useComparisonStream(1));
    act(() => {
      mockEsInstance!.triggerError();
    });
    expect(result.current.streamDone).toBe(true);
  });

  it("opens EventSource to the correct URL", () => {
    renderHook(() => useComparisonStream(42));
    expect(mockEsInstance?.url).toContain("/comparisons/42/stream");
  });

  it("does not open EventSource when comparisonId is null", () => {
    renderHook(() => useComparisonStream(null));
    expect(mockEsInstance).toBeNull();
  });
});
