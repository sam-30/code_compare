import { useEffect, useRef, useState } from "react";
import type { ComparisonStatus, MethodResult } from "../api/comparisons";

interface StreamState {
  methods: MethodResult[];
  status: ComparisonStatus;
  overallScore: number | null;
  streamDone: boolean;
}

const BASE_URL = import.meta.env.VITE_API_URL ?? "";

export function useComparisonStream(comparisonId: number | null): StreamState {
  const [state, setState] = useState<StreamState>({
    methods: [],
    status: "pending",
    overallScore: null,
    streamDone: false,
  });
  const esRef = useRef<EventSource | null>(null);

  useEffect(() => {
    if (comparisonId === null) return;

    // EventSource can't send Authorization headers, pass token as query param instead
    const token = localStorage.getItem("access_token");
    const qs = token ? `?token=${encodeURIComponent(token)}` : "";
    const es = new EventSource(
      `${BASE_URL}/comparisons/${comparisonId}/stream${qs}`
    );
    esRef.current = es;

    es.onmessage = (event) => {
      const data = JSON.parse(event.data) as Record<string, unknown>;

      if (data.type === "method") {
        setState((prev) => ({
          ...prev,
          status: "running",
          methods: prev.methods.some((m) => m.method_id === data.method_id)
            ? prev.methods
            : [
                ...prev.methods,
                {
                  method_id: data.method_id as string,
                  score: data.score as number,
                  weight: data.weight as number,
                  details: (data.details as Record<string, unknown>) ?? {},
                  duration_ms: (data.duration_ms as number) ?? 0,
                },
              ],
        }));
      } else if (data.type === "done") {
        setState((prev) => ({
          ...prev,
          status: "complete",
          overallScore: data.overall_score as number,
          streamDone: true,
        }));
        es.close();
      } else if (data.type === "error") {
        setState((prev) => ({ ...prev, status: "failed", streamDone: true }));
        es.close();
      }
    };

    es.onerror = () => {
      setState((prev) => ({ ...prev, streamDone: true }));
      es.close();
    };

    return () => {
      es.close();
    };
  }, [comparisonId]);

  return state;
}
