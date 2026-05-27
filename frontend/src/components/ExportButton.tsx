const BASE_URL = import.meta.env.VITE_API_URL ?? "";

interface ExportButtonProps {
  comparisonId: number;
}

export default function ExportButton({ comparisonId }: ExportButtonProps) {
  const download = (format: "json" | "pdf") => {
    const url = `${BASE_URL}/comparisons/${comparisonId}/export?format=${format}`;
    const a = document.createElement("a");
    a.href = url;
    a.download = `comparison_${comparisonId}.${format}`;
    a.click();
  };

  return (
    <div className="flex gap-2" data-testid="export-buttons">
      <button
        onClick={() => download("json")}
        className="rounded border border-gray-300 px-3 py-1.5 text-sm hover:bg-gray-50"
        aria-label="Export JSON"
      >
        Export JSON
      </button>
      <button
        onClick={() => download("pdf")}
        className="rounded border border-gray-300 px-3 py-1.5 text-sm hover:bg-gray-50"
        aria-label="Export PDF"
      >
        Export PDF
      </button>
    </div>
  );
}
