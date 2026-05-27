import { useQuery } from "@tanstack/react-query";
import { Link } from "react-router-dom";
import { comparisonsApi } from "../api/comparisons";
import StatusBadge from "../components/StatusBadge";

export default function HistoryPage() {
  const { data, isLoading, isError } = useQuery({
    queryKey: ["comparisons"],
    queryFn: comparisonsApi.list,
  });

  return (
    <div>
      <h1 className="text-2xl font-bold text-gray-900 mb-6">Comparison History</h1>

      {isLoading && (
        <p className="text-gray-400 text-sm">Loading…</p>
      )}

      {isError && (
        <p className="text-red-600 text-sm">Failed to load history.</p>
      )}

      {data && data.length === 0 && (
        <p data-testid="empty-history" className="text-gray-500 text-sm">
          No comparisons yet.{" "}
          <Link to="/" className="underline text-blue-600">
            Start one
          </Link>
          .
        </p>
      )}

      {data && data.length > 0 && (
        <div className="overflow-x-auto">
          <table className="w-full text-sm" data-testid="history-table">
            <thead>
              <tr className="text-left text-xs uppercase text-gray-500 border-b">
                <th className="py-2 pr-4">#</th>
                <th className="py-2 pr-4">Repos</th>
                <th className="py-2 pr-4">Language</th>
                <th className="py-2 pr-4">Score</th>
                <th className="py-2 pr-4">Status</th>
                <th className="py-2">Created</th>
              </tr>
            </thead>
            <tbody>
              {data.map((c) => (
                <tr
                  key={c.id}
                  data-testid={`history-row-${c.id}`}
                  className="border-b last:border-0 hover:bg-gray-50"
                >
                  <td className="py-2 pr-4">
                    <Link
                      to={`/comparisons/${c.id}`}
                      className="text-blue-600 underline font-mono"
                    >
                      #{c.id}
                    </Link>
                  </td>
                  <td className="py-2 pr-4 text-gray-700">
                    {c.repo_a_id} vs {c.repo_b_id}
                  </td>
                  <td className="py-2 pr-4 capitalize">{c.language}</td>
                  <td className="py-2 pr-4 tabular-nums">
                    {c.overall_score !== null
                      ? `${Math.round(c.overall_score * 100)}%`
                      : "—"}
                  </td>
                  <td className="py-2 pr-4">
                    <StatusBadge status={c.status} />
                  </td>
                  <td className="py-2 text-gray-500">
                    {new Date(c.created_at).toLocaleDateString()}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
