const styles: Record<string, string> = {
  pending: "bg-gray-100 text-gray-700",
  ingesting: "bg-blue-100 text-blue-700 animate-pulse",
  running: "bg-blue-100 text-blue-700 animate-pulse",
  ready: "bg-green-100 text-green-700",
  complete: "bg-green-100 text-green-700",
  failed: "bg-red-100 text-red-700",
};

export default function StatusBadge({ status }: { status: string }) {
  const cls = styles[status] ?? "bg-gray-100 text-gray-700";
  return (
    <span className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium ${cls}`}>
      {status}
    </span>
  );
}
