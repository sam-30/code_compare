import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import { comparisonsApi } from "../api/comparisons";
import { configsApi } from "../api/configs";
import { repositoriesApi } from "../api/repositories";
import StatusBadge from "../components/StatusBadge";

const LANGUAGES = [
  { value: "python", label: "Python" },
  { value: "javascript", label: "JavaScript / TypeScript" },
];

type SourceTab = "local" | "git" | "zip";

const TABS: { id: SourceTab; label: string }[] = [
  { id: "local", label: "Local Path" },
  { id: "git", label: "Git URL" },
  { id: "zip", label: "Upload ZIP" },
];

interface RepoInfo {
  id: number;
  language: string;
}

function RepositoryForm({
  label,
  onReady,
}: {
  label: string;
  onReady: (info: RepoInfo | null) => void;
}) {
  const [tab, setTab] = useState<SourceTab>("git");
  const [name, setName] = useState("");
  const [path, setPath] = useState("");
  const [url, setUrl] = useState("");
  const [language, setLanguage] = useState("python");
  const [repoId, setRepoId] = useState<number | null>(null);
  const fileRef = useRef<HTMLInputElement>(null);
  const queryClient = useQueryClient();

  const create = useMutation({
    mutationFn: repositoriesApi.create,
    onSuccess: (repo) => {
      setRepoId(repo.id);
      queryClient.invalidateQueries({ queryKey: ["repos"] });
    },
  });

  const upload = useMutation({
    mutationFn: ({ name, language, file }: { name: string; language: string; file: File }) =>
      repositoriesApi.upload(name, language, file),
    onSuccess: (repo) => {
      setRepoId(repo.id);
      queryClient.invalidateQueries({ queryKey: ["repos"] });
    },
  });

  const { data: repo } = useQuery({
    queryKey: ["repo", repoId],
    queryFn: () => repositoriesApi.get(repoId!),
    enabled: repoId !== null,
    refetchInterval: (q) => {
      const status = q.state.data?.status;
      if (status === "pending" || status === "ingesting") return 2000;
      if (status === "ready") {
        onReady({ id: repoId!, language });
        return false;
      }
      if (status === "failed") {
        onReady(null);
        return false;
      }
      return false;
    },
  });

  const isPending = create.isPending || upload.isPending;
  const error = create.error || upload.error;

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (tab === "local") {
      create.mutate({ name, path, language });
    } else if (tab === "git") {
      create.mutate({ name, language, source_type: "git", url });
    } else if (tab === "zip") {
      const file = fileRef.current?.files?.[0];
      if (!file) return;
      upload.mutate({ name, language, file });
    }
  };

  const reset = () => {
    setRepoId(null);
    setName("");
    setPath("");
    setUrl("");
    onReady(null);
  };

  return (
    <div className="bg-white rounded-lg border border-gray-200 p-5">
      <h2 className="font-semibold text-gray-800 mb-4">{label}</h2>

      {!repoId ? (
        <>
          <div className="flex gap-1 mb-4 border-b" role="tablist" aria-label="Source type">
            {TABS.map((t) => (
              <button
                key={t.id}
                type="button"
                role="tab"
                aria-selected={tab === t.id}
                data-testid={`tab-${t.id}`}
                onClick={() => setTab(t.id)}
                className={`px-3 py-1.5 text-sm rounded-t border-b-2 -mb-px transition-colors ${
                  tab === t.id
                    ? "border-blue-600 text-blue-600 font-medium"
                    : "border-transparent text-gray-500 hover:text-gray-700"
                }`}
              >
                {t.label}
              </button>
            ))}
          </div>

          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Name</label>
              <input
                className="w-full border rounded px-3 py-2 text-sm"
                value={name}
                onChange={(e) => setName(e.target.value)}
                placeholder="e.g. my-project"
                required
              />
            </div>

            {tab === "local" && (
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Folder path (absolute)
                </label>
                <input
                  className="w-full border rounded px-3 py-2 text-sm font-mono"
                  value={path}
                  onChange={(e) => setPath(e.target.value)}
                  placeholder="/path/to/codebase"
                  required
                />
              </div>
            )}

            {tab === "git" && (
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Git URL</label>
                <input
                  className="w-full border rounded px-3 py-2 text-sm font-mono"
                  value={url}
                  onChange={(e) => setUrl(e.target.value)}
                  placeholder="https://github.com/org/repo.git"
                  required
                />
              </div>
            )}

            {tab === "zip" && (
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">ZIP archive</label>
                <input
                  ref={fileRef}
                  type="file"
                  accept=".zip"
                  className="w-full text-sm"
                  required
                />
              </div>
            )}

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Language</label>
              <select
                className="w-full border rounded px-3 py-2 text-sm"
                value={language}
                onChange={(e) => setLanguage(e.target.value)}
              >
                {LANGUAGES.map((l) => (
                  <option key={l.value} value={l.value}>{l.label}</option>
                ))}
              </select>
            </div>

            {error && (
              <p className="text-sm text-red-600">
                {(error as { response?: { data?: { detail?: string } } })?.response?.data?.detail ??
                  "An error occurred"}
              </p>
            )}

            <button
              type="submit"
              disabled={isPending}
              className="w-full bg-blue-600 text-white py-2 px-4 rounded text-sm font-medium hover:bg-blue-700 disabled:opacity-50"
            >
              {isPending ? "Registering…" : "Register Repository"}
            </button>
          </form>
        </>
      ) : (
        <div className="space-y-3">
          <div className="flex items-center justify-between">
            <span className="font-medium text-gray-800">{repo?.name ?? "…"}</span>
            {repo && <StatusBadge status={repo.status} />}
          </div>
          <p className="text-xs text-gray-500 font-mono truncate">{repo?.path}</p>
          {repo?.status === "ready" && (
            <p className="text-sm text-green-700">{repo.file_count} files indexed ✓</p>
          )}
          {(repo?.status === "pending" || repo?.status === "ingesting") && (
            <p className="text-sm text-blue-600 animate-pulse">Indexing files…</p>
          )}
          {repo?.status === "failed" && (
            <p className="text-sm text-red-600">{repo.error_message}</p>
          )}
          <button onClick={reset} className="text-xs text-blue-600 hover:underline">
            Change repository
          </button>
        </div>
      )}
    </div>
  );
}

function RunComparisonPanel({ repoA, repoB }: { repoA: RepoInfo; repoB: RepoInfo }) {
  const navigate = useNavigate();
  const [configId, setConfigId] = useState<number | "default">("default");

  const { data: configs } = useQuery({
    queryKey: ["configs"],
    queryFn: configsApi.list,
  });

  const run = useMutation({
    mutationFn: comparisonsApi.create,
    onSuccess: (cmp) => navigate(`/comparisons/${cmp.id}`),
  });

  const handleRun = () => {
    const payload: Parameters<typeof comparisonsApi.create>[0] = {
      repo_a_id: repoA.id,
      repo_b_id: repoB.id,
      language: repoA.language,
    };
    if (configId !== "default" && typeof configId === "number") {
      payload.config_id = configId;
    }
    run.mutate(payload);
  };

  return (
    <div className="mt-8 bg-blue-50 border border-blue-200 rounded-lg p-6">
      <h2 className="text-lg font-semibold text-blue-900 mb-1">Both repositories are ready</h2>
      <p className="text-sm text-blue-700 mb-5">
        Select a comparison preset (optional) then run to generate a similarity report.
      </p>

      <div className="flex flex-col sm:flex-row gap-4 items-end">
        <div className="flex-1">
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Comparison preset
          </label>
          <select
            className="w-full border rounded px-3 py-2 text-sm"
            value={configId}
            onChange={(e) =>
              setConfigId(e.target.value === "default" ? "default" : Number(e.target.value))
            }
          >
            <option value="default">Default (all methods, equal weights)</option>
            {configs?.map((c) => (
              <option key={c.id} value={c.id}>
                {c.name}
              </option>
            ))}
          </select>
        </div>

        <button
          onClick={handleRun}
          disabled={run.isPending}
          className="sm:w-48 bg-blue-600 text-white py-2 px-6 rounded text-sm font-medium hover:bg-blue-700 disabled:opacity-50 whitespace-nowrap"
        >
          {run.isPending ? "Starting…" : "Run Comparison →"}
        </button>
      </div>

      {run.isError && (
        <p className="mt-3 text-sm text-red-600">
          {(run.error as { response?: { data?: { detail?: string } } })?.response?.data?.detail ??
            "Failed to start comparison"}
        </p>
      )}
    </div>
  );
}

export default function NewComparisonPage() {
  const [repoA, setRepoA] = useState<RepoInfo | null>(null);
  const [repoB, setRepoB] = useState<RepoInfo | null>(null);

  const bothReady = repoA !== null && repoB !== null;

  return (
    <div>
      <h1 className="text-2xl font-bold text-gray-900 mb-2">New Comparison</h1>
      <p className="text-sm text-gray-500 mb-8">
        Register two codebases then click <strong>Run Comparison</strong> to generate a similarity
        report.
      </p>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <RepositoryForm label="Reference Repository (Repo A)" onReady={setRepoA} />
        <RepositoryForm label="Suspect Repository (Repo B)" onReady={setRepoB} />
      </div>

      {!bothReady && (repoA || repoB) && (
        <p className="mt-6 text-sm text-gray-500 text-center">
          Waiting for{" "}
          {!repoA && !repoB
            ? "both repositories"
            : !repoA
            ? "Repo A"
            : "Repo B"}{" "}
          to finish indexing…
        </p>
      )}

      {bothReady && <RunComparisonPanel repoA={repoA} repoB={repoB} />}
    </div>
  );
}
