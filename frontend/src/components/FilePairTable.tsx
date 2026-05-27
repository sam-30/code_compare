import { useState } from "react";
import type { FileMatch } from "../api/comparisons";

interface FilePairTableProps {
  matches: FileMatch[];
}

type SortKey = "similarity_score" | "file_a_path" | "file_b_path" | "method_id";

export default function FilePairTable({ matches }: FilePairTableProps) {
  const [sortKey, setSortKey] = useState<SortKey>("similarity_score");
  const [sortDesc, setSortDesc] = useState(true);

  if (matches.length === 0) {
    return (
      <p data-testid="no-matches" className="text-sm text-gray-500">
        No file-pair matches recorded.
      </p>
    );
  }

  const sorted = [...matches].sort((a, b) => {
    const av = a[sortKey];
    const bv = b[sortKey];
    if (typeof av === "number" && typeof bv === "number") {
      return sortDesc ? bv - av : av - bv;
    }
    const as = String(av);
    const bs = String(bv);
    return sortDesc ? bs.localeCompare(as) : as.localeCompare(bs);
  });

  const handleSort = (key: SortKey) => {
    if (key === sortKey) {
      setSortDesc((d) => !d);
    } else {
      setSortKey(key);
      setSortDesc(true);
    }
  };

  const th = (key: SortKey, label: string) => (
    <th
      className="text-left py-2 px-3 text-xs uppercase text-gray-500 cursor-pointer select-none"
      onClick={() => handleSort(key)}
    >
      {label}
      {sortKey === key && (
        <span className="ml-1">{sortDesc ? "↓" : "↑"}</span>
      )}
    </th>
  );

  return (
    <div data-testid="file-pair-table" className="overflow-x-auto">
      <table className="w-full text-sm">
        <thead className="border-b">
          <tr>
            {th("file_a_path", "File A")}
            {th("file_b_path", "File B")}
            {th("similarity_score", "Score")}
            {th("method_id", "Method")}
          </tr>
        </thead>
        <tbody>
          {sorted.map((m, i) => (
            <tr key={i} className="border-b last:border-0 hover:bg-gray-50">
              <td className="py-1.5 px-3 font-mono text-xs truncate max-w-xs" title={m.file_a_path}>
                {m.file_a_path.split("/").slice(-2).join("/")}
              </td>
              <td className="py-1.5 px-3 font-mono text-xs truncate max-w-xs" title={m.file_b_path}>
                {m.file_b_path.split("/").slice(-2).join("/")}
              </td>
              <td className="py-1.5 px-3 tabular-nums">
                {Math.round(m.similarity_score * 100)}%
              </td>
              <td className="py-1.5 px-3 text-gray-500">{m.method_id}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
