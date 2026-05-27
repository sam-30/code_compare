import { useMutation, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { configsApi, CreateConfigPayload } from "../api/configs";

interface MethodDef {
  id: string;
  label: string;
  defaultWeight: number;
}

const ALL_METHODS: MethodDef[] = [
  { id: "file_hash", label: "Exact File Hash", defaultWeight: 15 },
  { id: "line_similarity", label: "Line Similarity %", defaultWeight: 20 },
  { id: "function_names", label: "Function Name Overlap", defaultWeight: 15 },
  { id: "ast_structure", label: "AST Structural Similarity", defaultWeight: 20 },
  { id: "token_ngram", label: "Token N-gram Fingerprinting", defaultWeight: 20 },
  { id: "call_graph", label: "Call Graph / Logic Tracing", defaultWeight: 10 },
  { id: "import_analysis", label: "Import / Dependency Profile", defaultWeight: 5 },
  { id: "identifier_similarity", label: "Variable / Identifier Names", defaultWeight: 5 },
  { id: "complexity_profile", label: "Cyclomatic Complexity Profile", defaultWeight: 5 },
];

interface MethodState {
  enabled: boolean;
  weight: number;
}

interface ConfigEditorProps {
  onSaved?: (id: number) => void;
}

export default function ConfigEditor({ onSaved }: ConfigEditorProps) {
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [methods, setMethods] = useState<Record<string, MethodState>>(
    Object.fromEntries(
      ALL_METHODS.map((m) => [m.id, { enabled: true, weight: m.defaultWeight }])
    )
  );

  const queryClient = useQueryClient();
  const mutation = useMutation({
    mutationFn: (payload: CreateConfigPayload) => configsApi.create(payload),
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ["configs"] });
      onSaved?.(data.id);
    },
  });

  const enabledMethods = ALL_METHODS.filter((m) => methods[m.id].enabled);
  const totalRawWeight = enabledMethods.reduce(
    (sum, m) => sum + methods[m.id].weight,
    0
  );

  const normalizedPct = (id: string): number => {
    if (!methods[id].enabled || totalRawWeight === 0) return 0;
    return Math.round((methods[id].weight / totalRawWeight) * 100);
  };

  const handleToggle = (id: string) => {
    setMethods((prev) => ({
      ...prev,
      [id]: { ...prev[id], enabled: !prev[id].enabled },
    }));
  };

  const handleWeight = (id: string, value: number) => {
    setMethods((prev) => ({
      ...prev,
      [id]: { ...prev[id], weight: value },
    }));
  };

  const handleSave = () => {
    if (!name.trim() || enabledMethods.length === 0) return;
    const rawWeights: Record<string, number> = {};
    enabledMethods.forEach((m) => {
      rawWeights[m.id] = methods[m.id].weight;
    });
    mutation.mutate({ name: name.trim(), description: description.trim(), method_weights: rawWeights });
  };

  const canSave = name.trim().length > 0 && enabledMethods.length > 0 && !mutation.isPending;

  return (
    <div data-testid="config-editor" className="space-y-4">
      <div>
        <label htmlFor="config-name" className="block text-sm font-medium">
          Preset Name
        </label>
        <input
          id="config-name"
          className="mt-1 block w-full rounded border px-3 py-2 text-sm"
          value={name}
          onChange={(e) => setName(e.target.value)}
          placeholder="e.g. Strict IP Comparison"
        />
      </div>
      <div>
        <label htmlFor="config-desc" className="block text-sm font-medium">
          Description
        </label>
        <input
          id="config-desc"
          className="mt-1 block w-full rounded border px-3 py-2 text-sm"
          value={description}
          onChange={(e) => setDescription(e.target.value)}
          placeholder="Optional description"
        />
      </div>

      <table className="w-full text-sm">
        <thead>
          <tr className="text-left text-xs uppercase text-gray-500">
            <th className="pb-2">Method</th>
            <th className="pb-2">Enabled</th>
            <th className="pb-2">Weight</th>
            <th className="pb-2 text-right">%</th>
          </tr>
        </thead>
        <tbody>
          {ALL_METHODS.map((m) => (
            <tr key={m.id} data-testid={`method-row-${m.id}`} className="border-t">
              <td className="py-2 pr-4">{m.label}</td>
              <td className="py-2">
                <input
                  type="checkbox"
                  aria-label={`Enable ${m.label}`}
                  checked={methods[m.id].enabled}
                  onChange={() => handleToggle(m.id)}
                />
              </td>
              <td className="py-2 pr-2 w-48">
                <input
                  type="range"
                  aria-label={`Weight for ${m.label}`}
                  min={1}
                  max={100}
                  value={methods[m.id].weight}
                  disabled={!methods[m.id].enabled}
                  onChange={(e) => handleWeight(m.id, Number(e.target.value))}
                  className="w-full"
                />
              </td>
              <td className="py-2 text-right tabular-nums w-12">
                {normalizedPct(m.id)}%
              </td>
            </tr>
          ))}
        </tbody>
      </table>

      <div className="flex items-center gap-3">
        <button
          onClick={handleSave}
          disabled={!canSave}
          className="rounded bg-blue-600 px-4 py-2 text-sm font-medium text-white disabled:opacity-50"
        >
          {mutation.isPending ? "Saving…" : "Save Preset"}
        </button>
        {mutation.isError && (
          <span className="text-sm text-red-600">Error saving config.</span>
        )}
        {mutation.isSuccess && (
          <span className="text-sm text-green-600">Preset saved!</span>
        )}
      </div>
    </div>
  );
}
