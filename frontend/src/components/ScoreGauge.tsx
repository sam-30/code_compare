import { PieChart, Pie, Cell } from "recharts";

interface ScoreGaugeProps {
  score: number | null;
  size?: number;
}

function scoreColor(score: number): string {
  if (score < 0.3) return "#22c55e"; // green
  if (score < 0.7) return "#f59e0b"; // yellow
  return "#ef4444";                  // red
}

function scoreLabel(score: number): string {
  if (score < 0.3) return "Low Similarity";
  if (score < 0.7) return "Moderate Similarity";
  return "High Similarity";
}

export default function ScoreGauge({ score, size = 220 }: ScoreGaugeProps) {
  if (score === null) {
    return (
      <div
        data-testid="score-gauge"
        style={{ width: size, height: size / 2 + 40 }}
        className="flex items-center justify-center text-gray-400 text-sm"
      >
        Calculating…
      </div>
    );
  }

  const color = scoreColor(score);
  const pct = Math.round(score * 100);
  const cx = size / 2;
  const cy = size / 2;
  const innerR = size * 0.28;
  const outerR = size * 0.37;

  const data = [
    { value: score },
    { value: 1 - score },
  ];

  return (
    <div
      data-testid="score-gauge"
      className="flex flex-col items-center"
      style={{ width: size }}
    >
      <div className="relative" style={{ width: size, height: cy + outerR + 8 }}>
        <PieChart width={size} height={cy + outerR + 8}>
          <Pie
            data={data}
            cx={cx}
            cy={cy}
            startAngle={180}
            endAngle={0}
            innerRadius={innerR}
            outerRadius={outerR}
            dataKey="value"
            strokeWidth={0}
          >
            <Cell fill={color} />
            <Cell fill="#e5e7eb" />
          </Pie>
        </PieChart>
        {/* Centre label */}
        <div
          className="absolute inset-0 flex flex-col items-center justify-end pb-1"
          style={{ bottom: 0 }}
        >
          <span
            data-testid="score-pct"
            className="text-3xl font-bold leading-none"
            style={{ color }}
          >
            {pct}%
          </span>
        </div>
      </div>
      <span
        data-testid="score-label"
        className="mt-1 text-sm font-medium"
        style={{ color }}
      >
        {scoreLabel(score)}
      </span>
    </div>
  );
}
