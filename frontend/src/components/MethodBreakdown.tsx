import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  Cell,
  ResponsiveContainer,
} from "recharts";
import type { MethodResult } from "../api/comparisons";

interface MethodBreakdownProps {
  methods: MethodResult[];
}

const METHOD_LABELS: Record<string, string> = {
  file_hash: "File Hash",
  line_similarity: "Line Similarity",
  function_names: "Function Names",
  ast_structure: "AST Structure",
  token_ngram: "Token N-gram",
  call_graph: "Call Graph",
  import_analysis: "Import Analysis",
  identifier_similarity: "Identifiers",
  complexity_profile: "Complexity",
};

function barColor(score: number): string {
  if (score < 0.3) return "#22c55e";
  if (score < 0.7) return "#f59e0b";
  return "#ef4444";
}

function pctStr(v: number): string {
  return `${Math.round(v * 100)}%`;
}

export default function MethodBreakdown({ methods }: MethodBreakdownProps) {
  const sorted = [...methods].sort((a, b) => b.score - a.score);
  const chartData = sorted.map((m) => ({
    name: METHOD_LABELS[m.method_id] ?? m.method_id,
    score: m.score,
    weight: m.weight,
    method_id: m.method_id,
  }));

  return (
    <div data-testid="method-breakdown">
      <ResponsiveContainer width="100%" height={Math.max(200, methods.length * 42)}>
        <BarChart data={chartData} layout="vertical" margin={{ left: 16, right: 40 }}>
          <XAxis type="number" domain={[0, 1]} tickFormatter={pctStr} fontSize={11} />
          <YAxis
            type="category"
            dataKey="name"
            width={110}
            fontSize={11}
            tick={{ fill: "#374151" }}
          />
          <Tooltip
            formatter={(value: number) => [pctStr(value), "Score"]}
            labelFormatter={(label) => label}
          />
          <Bar dataKey="score" radius={[0, 3, 3, 0]}>
            {chartData.map((entry) => (
              <Cell
                key={entry.method_id}
                fill={barColor(entry.score)}
                data-testid={`bar-${entry.method_id}`}
              />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>

      {/* Tabular breakdown for accessibility / testing */}
      <table className="w-full mt-4 text-sm" data-testid="method-table">
        <thead>
          <tr className="text-xs uppercase text-gray-500 border-b">
            <th className="text-left py-1 pr-4">Method</th>
            <th className="text-right py-1 pr-4">Score</th>
            <th className="text-right py-1">Weight</th>
          </tr>
        </thead>
        <tbody>
          {sorted.map((m) => (
            <tr key={m.method_id} data-testid={`method-row-${m.method_id}`} className="border-b last:border-0">
              <td className="py-1.5 pr-4">{METHOD_LABELS[m.method_id] ?? m.method_id}</td>
              <td
                className="py-1.5 pr-4 text-right font-mono"
                data-testid={`score-${m.method_id}`}
              >
                {pctStr(m.score)}
              </td>
              <td className="py-1.5 text-right font-mono text-gray-500">
                {Math.round(m.weight * 100)}%
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
