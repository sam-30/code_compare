import { useQuery } from "@tanstack/react-query";
import { useParams, Link } from "react-router-dom";
import { comparisonsApi } from "../api/comparisons";
import FilePairTable from "../components/FilePairTable";
import MethodBreakdown from "../components/MethodBreakdown";
import ScoreGauge from "../components/ScoreGauge";
import StatusBadge from "../components/StatusBadge";
import ExportButton from "../components/ExportButton";
import { useComparisonStream } from "../hooks/useComparisonStream";

const ALL_METHOD_COUNT = 9;

export default function ResultsPage() {
  const { id } = useParams<{ id: string }>();
  const compId = Number(id);

  const { methods: streamMethods, status: streamStatus, overallScore: streamScore, streamDone } =
    useComparisonStream(isNaN(compId) ? null : compId);

  // Load full details (repo IDs, file matches) once streaming is done.
  const { data } = useQuery({
    queryKey: ["comparison", compId],
    queryFn: () => comparisonsApi.get(compId),
    enabled: !isNaN(compId) && streamDone,
  });

  const isRunning = streamStatus === "pending" || streamStatus === "running";
  const score = streamDone ? (data?.overall_score ?? streamScore) : null;
  const methods = streamDone ? (data?.method_results ?? streamMethods) : streamMethods;
  const fileMatches = data?.file_matches ?? [];

  return (
    <div className="space-y-8">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-gray-900">
          Comparison #{isNaN(compId) ? id : compId}
        </h1>
        <div className="flex items-center gap-3">
          {streamDone && <ExportButton comparisonId={compId} />}
          <StatusBadge status={streamStatus} />
        </div>
      </div>

      {/* Live progress bar while running */}
      {isRunning && (
        <div className="space-y-1" data-testid="progress-bar-container">
          <div className="flex justify-between text-sm text-gray-500">
            <span>Analysing…</span>
            <span data-testid="progress-count">
              {streamMethods.length} / {ALL_METHOD_COUNT} methods
            </span>
          </div>
          <div className="h-2 w-full rounded bg-gray-200 overflow-hidden">
            <div
              className="h-full bg-blue-500 transition-all"
              style={{ width: `${(streamMethods.length / ALL_METHOD_COUNT) * 100}%` }}
              data-testid="progress-fill"
            />
          </div>

          {/* Reveal methods as they arrive */}
          {streamMethods.length > 0 && (
            <div className="pt-2">
              <MethodBreakdown methods={streamMethods} />
            </div>
          )}
        </div>
      )}

      {/* Final results */}
      {streamDone && (
        <>
          {streamStatus === "failed" && data?.error_message && (
            <div className="rounded bg-red-50 border border-red-200 p-4 text-sm text-red-700">
              {data.error_message}
            </div>
          )}

          <div className="flex flex-col sm:flex-row gap-8 items-start">
            <div className="flex-shrink-0">
              <h2 className="text-sm font-semibold text-gray-600 mb-2">Overall Score</h2>
              <ScoreGauge score={score} />
            </div>
            {data && (
              <div className="flex-1 min-w-0">
                <h2 className="text-sm font-semibold text-gray-600 mb-2">Details</h2>
                <dl className="grid grid-cols-2 gap-x-4 gap-y-2 text-sm">
                  <dt className="text-gray-500">Language</dt>
                  <dd className="font-medium capitalize">{data.language}</dd>
                  <dt className="text-gray-500">Repository A</dt>
                  <dd className="font-mono text-xs">{data.repo_a_id}</dd>
                  <dt className="text-gray-500">Repository B</dt>
                  <dd className="font-mono text-xs">{data.repo_b_id}</dd>
                  {data.completed_at && (
                    <>
                      <dt className="text-gray-500">Completed</dt>
                      <dd>{new Date(data.completed_at).toLocaleString()}</dd>
                    </>
                  )}
                </dl>
              </div>
            )}
          </div>

          {methods.length > 0 && (
            <section>
              <h2 className="text-lg font-semibold text-gray-800 mb-3">Method Breakdown</h2>
              <MethodBreakdown methods={methods} />
            </section>
          )}

          <section>
            <h2 className="text-lg font-semibold text-gray-800 mb-3">File-Pair Matches</h2>
            <FilePairTable matches={fileMatches} />
          </section>
        </>
      )}

      {!isRunning && !streamDone && (
        <p className="text-gray-400 text-sm">
          Could not load comparison.{" "}
          <Link to="/" className="underline text-blue-600">Go back</Link>
        </p>
      )}
    </div>
  );
}
