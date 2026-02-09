import { useEffect, useState, type ComponentType } from 'react';
import {
  Activity,
  AlertTriangle,
  ArrowLeft,
  CheckCircle,
  FolderPlus,
  FolderSearch,
  GitBranch,
  Lightbulb,
  Play,
  RefreshCw,
  Search,
  Terminal,
} from 'lucide-react';

import { API_BASE } from './config';

type VaultRunResult = {
  argv: string[];
  exit_code: number;
  stdout: string;
  stderr: string;
  truncated: boolean;
  ok: boolean;
};

type Project = {
  id: string;
  name: string;
  objective: string;
  status: string;
  created_at: string;
  priority: number;
};

async function apiJson<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`,
    {
      ...init,
      credentials: 'include',
      headers: {
        'Content-Type': 'application/json',
        ...(init?.headers || {}),
      },
    },
  );

  if (!res.ok) {
    const text = await res.text();
    throw new Error(`${res.status}: ${text}`);
  }

  return res.json();
}

async function runVaultGet(endpoint: string): Promise<VaultRunResult> {
  return apiJson<VaultRunResult>(endpoint, { method: 'GET' });
}

async function runVaultPost(endpoint: string, payload?: unknown): Promise<VaultRunResult> {
  return apiJson<VaultRunResult>(endpoint, {
    method: 'POST',
    body: JSON.stringify(payload ?? {}),
  });
}

function CommandOutput({ result }: { result: VaultRunResult | null }) {
  if (!result) {
    return <div className="text-gray-400 italic text-sm p-4">No commands executed yet.</div>;
  }

  const cmd = result.argv.length >= 3 ? result.argv.slice(2).join(' ') : result.argv.join(' ');

  return (
    <div className="bg-gray-900 text-gray-100 p-4 rounded-md font-mono text-xs overflow-auto max-h-72 border border-gray-800 shadow-inner">
      <div className="flex gap-2 mb-2 border-b border-gray-800 pb-2">
        <span className="text-green-400">$ {cmd}</span>
        <span className={result.exit_code === 0 ? 'text-gray-500' : 'text-red-400'}>(exit {result.exit_code}{result.truncated ? ', truncated' : ''})</span>
      </div>
      {result.stderr && (
        <pre className="text-red-300 whitespace-pre-wrap mb-2">{result.stderr}</pre>
      )}
      <pre className="text-gray-200 whitespace-pre-wrap">{result.stdout}</pre>
    </div>
  );
}

function EntryScreen({
  onSelectProject,
  setLastResult,
}: {
  onSelectProject: (id: string) => void;
  setLastResult: (r: VaultRunResult) => void;
}) {
  const [projects, setProjects] = useState<Project[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const [showNew, setShowNew] = useState(false);
  const [newId, setNewId] = useState('');
  const [newName, setNewName] = useState('');
  const [newObjective, setNewObjective] = useState('');
  const [newPriority, setNewPriority] = useState(0);

  const [searchQuery, setSearchQuery] = useState('');

  async function handleListProjects(showInConsole: boolean) {
    setError(null);
    setLoading(true);
    try {
      const res = await runVaultGet('/vault/list');
      if (showInConsole) setLastResult(res);

      if (!res.ok) {
        throw new Error(res.stderr || 'vault list failed');
      }

      const parsed = JSON.parse(res.stdout) as Project[];
      setProjects(parsed);
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : String(e);
      setError(msg);
    } finally {
      setLoading(false);
    }
  }

  async function handleInit() {
    setError(null);
    setLoading(true);
    try {
      const res = await runVaultPost('/vault/init', {
        id: newId,
        name: newName || null,
        objective: newObjective,
        priority: newPriority,
      });
      setLastResult(res);

      if (!res.ok) {
        throw new Error(res.stderr || 'vault init failed');
      }

      // Keep "one click = one CLI command": update UI optimistically (no extra list command).
      const nowIso = new Date().toISOString();
      setProjects((prev) => {
        const next: Project[] = [
          {
            id: newId,
            name: newName || newId,
            objective: newObjective,
            status: 'active',
            created_at: nowIso,
            priority: newPriority,
          },
          ...prev.filter((p) => p.id !== newId),
        ];
        return next;
      });

      setShowNew(false);
      setNewId('');
      setNewName('');
      setNewObjective('');
      setNewPriority(0);
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : String(e);
      setError(msg);
    } finally {
      setLoading(false);
    }
  }

  async function handleSearch() {
    setError(null);
    setLoading(true);
    try {
      const res = await runVaultPost('/vault/search', { query: searchQuery });
      setLastResult(res);
      if (!res.ok) throw new Error(res.stderr || 'vault search failed');
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : String(e);
      setError(msg);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    // Load once to populate the table, but do not spam the console.
    handleListProjects(false).catch(() => undefined);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  return (
    <div className="space-y-6">
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <button
          onClick={() => handleListProjects(true)}
          className="flex items-center justify-center gap-2 p-4 bg-white border border-gray-200 rounded-lg shadow-sm hover:bg-gray-50 transition"
        >
          <RefreshCw className="w-5 h-5 text-blue-600" />
          <span className="font-semibold text-gray-800">LIST</span>
        </button>

        <button
          onClick={() => setShowNew((v) => !v)}
          className="flex items-center justify-center gap-2 p-4 bg-white border border-gray-200 rounded-lg shadow-sm hover:bg-gray-50 transition"
        >
          <FolderPlus className="w-5 h-5 text-green-600" />
          <span className="font-semibold text-gray-800">NEW PROJECT</span>
        </button>

        <div className="flex p-0 bg-white border border-gray-200 rounded-lg shadow-sm overflow-hidden">
          <input
            className="flex-1 p-4 outline-none"
            placeholder="SEARCH (vault search)"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === 'Enter') handleSearch();
            }}
          />
          <button
            onClick={handleSearch}
            className="px-4 hover:bg-gray-50"
            disabled={!searchQuery.trim() || loading}
            aria-label="Search"
          >
            <Search className="w-5 h-5 text-purple-600" />
          </button>
        </div>
      </div>

      {showNew && (
        <div className="bg-gray-50 border border-gray-200 p-4 rounded-lg">
          <div className="flex items-center gap-2 mb-3">
            <FolderSearch className="w-4 h-4 text-gray-600" />
            <div className="font-bold text-gray-700">Initialize New Project</div>
          </div>

          <div className="grid grid-cols-1 gap-3">
            <input
              className="w-full p-2 border border-gray-300 rounded"
              placeholder="Project ID (required)"
              value={newId}
              onChange={(e) => setNewId(e.target.value)}
            />
            <input
              className="w-full p-2 border border-gray-300 rounded"
              placeholder="Name (optional)"
              value={newName}
              onChange={(e) => setNewName(e.target.value)}
            />
            <textarea
              className="w-full p-2 border border-gray-300 rounded h-24"
              placeholder="Objective (required)"
              value={newObjective}
              onChange={(e) => setNewObjective(e.target.value)}
            />
            <input
              className="w-full p-2 border border-gray-300 rounded"
              type="number"
              value={newPriority}
              onChange={(e) => setNewPriority(parseInt(e.target.value || '0', 10))}
            />

            <div className="flex justify-end gap-2">
              <button
                type="button"
                onClick={() => setShowNew(false)}
                className="px-3 py-1 text-gray-600 hover:text-gray-900"
              >
                Cancel
              </button>
              <button
                type="button"
                onClick={handleInit}
                disabled={!newId.trim() || !newObjective.trim() || loading}
                className="px-3 py-1 bg-blue-600 text-white rounded hover:bg-blue-700 disabled:opacity-50"
              >
                Initialize
              </button>
            </div>
          </div>
        </div>
      )}

      {error && (
        <div className="border border-red-200 bg-red-50 text-red-800 text-sm p-3 rounded">
          {error}
        </div>
      )}

      <div className="bg-white border border-gray-200 rounded-lg shadow-sm overflow-hidden">
        <div className="px-4 py-2 border-b border-gray-200 flex items-center justify-between">
          <div className="font-semibold text-gray-800">Projects</div>
          <div className="text-xs text-gray-500">
            {loading ? 'Loading…' : `${projects.length} total`}
          </div>
        </div>

        <table className="w-full text-left">
          <thead className="bg-gray-50 border-b border-gray-200">
            <tr>
              <th className="p-3 font-semibold text-gray-600 text-sm">ID</th>
              <th className="p-3 font-semibold text-gray-600 text-sm">Objective</th>
              <th className="p-3 font-semibold text-gray-600 text-sm">Status</th>
              <th className="p-3 font-semibold text-gray-600 text-sm">Pri</th>
              <th className="p-3 font-semibold text-gray-600 text-sm">Created</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-100">
            {projects.map((p) => (
              <tr
                key={p.id}
                onClick={() => onSelectProject(p.id)}
                className="hover:bg-blue-50 cursor-pointer transition"
              >
                <td className="p-3 font-mono text-sm text-blue-700 font-semibold">{p.id}</td>
                <td className="p-3 text-sm text-gray-700 truncate max-w-xs">{p.objective}</td>
                <td className="p-3 text-sm">
                  <span
                    className={`px-2 py-0.5 rounded-full text-xs font-medium ${
                      p.status === 'active'
                        ? 'bg-green-100 text-green-800'
                        : p.status === 'completed'
                          ? 'bg-blue-100 text-blue-800'
                          : p.status === 'failed'
                            ? 'bg-red-100 text-red-800'
                            : 'bg-gray-100 text-gray-800'
                    }`}
                  >
                    {p.status}
                  </span>
                </td>
                <td className="p-3 text-sm text-gray-500">{p.priority}</td>
                <td className="p-3 text-sm text-gray-400">
                  {p.created_at ? new Date(p.created_at).toLocaleDateString() : ''}
                </td>
              </tr>
            ))}

            {!loading && projects.length === 0 && (
              <tr>
                <td colSpan={5} className="p-8 text-center text-gray-500">
                  No projects loaded. Click LIST.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}

function ProjectDetail({
  projectId,
  onBack,
  setLastResult,
  devMode,
}: {
  projectId: string;
  onBack: () => void;
  setLastResult: (r: VaultRunResult) => void;
  devMode: boolean;
}) {
  const [tab, setTab] = useState<'status' | 'insights' | 'verification' | 'branches'>('status');

  // Dev Mode inputs (low-level commands)
  const [watchType, setWatchType] = useState<'url' | 'query'>('url');
  const [watchTarget, setWatchTarget] = useState('');
  const watchInterval = 3600;
  const watchTags = '';

  const [cacheQuery, setCacheQuery] = useState('');
  const [cacheSetJson, setCacheSetJson] = useState('{}');

  async function run(endpoint: string, payload?: unknown) {
    const res = await runVaultPost(endpoint, payload);
    setLastResult(res);
  }

  function TabButton({
    id,
    label,
    icon: Icon,
  }: {
    id: 'status' | 'insights' | 'verification' | 'branches';
    label: string;
    icon: ComponentType<{ className?: string }>;
  }) {
    const active = tab === id;
    return (
      <button
        onClick={() => setTab(id)}
        className={`flex items-center gap-2 px-4 py-2 border-b-2 transition whitespace-nowrap ${
          active ? 'border-blue-600 text-blue-700' : 'border-transparent text-gray-500 hover:text-gray-700'
        }`}
      >
        <Icon className="w-4 h-4" />
        <span className="font-medium">{label}</span>
      </button>
    );
  }

  return (
    <div className="flex flex-col h-full">
      <div className="flex items-center gap-4 mb-6">
        <button onClick={onBack} className="p-2 hover:bg-gray-200 rounded-full" aria-label="Back">
          <ArrowLeft className="w-5 h-5" />
        </button>
        <div>
          <div className="text-xs text-gray-500">Project</div>
          <h1 className="text-2xl font-bold text-gray-800 font-mono">{projectId}</h1>
        </div>
      </div>

      <div className="flex gap-1 border-b border-gray-200 mb-6 overflow-x-auto">
        <TabButton id="status" label="Status" icon={Activity} />
        <TabButton id="insights" label="Insights" icon={Lightbulb} />
        <TabButton id="verification" label="Verification" icon={CheckCircle} />
        <TabButton id="branches" label="Branches" icon={GitBranch} />
      </div>

      <div className="flex-1 overflow-auto">
        {tab === 'status' && (
          <div className="space-y-4">
            <button
              onClick={() => run('/vault/status', { id: projectId })}
              className="border border-gray-300 bg-white px-4 py-2 rounded hover:bg-gray-50 text-sm"
            >
              Run: vault status
            </button>

            {devMode && (
              <div className="border border-yellow-300 bg-yellow-50 p-4 rounded space-y-4">
                <div className="font-bold text-yellow-900 text-sm flex items-center gap-2">
                  <Terminal className="w-4 h-4" />
                  Advanced / Dev Mode Actions
                </div>

                {/* Log */}
                <div className="border-t border-yellow-200 pt-2">
                  <div className="text-[10px] font-bold text-yellow-700 uppercase mb-2">Manual Event Log</div>
                  <button
                    onClick={() => run('/vault/log', { id: projectId, type: 'NOTE', step: 0, payload: {}, conf: 1.0, source: 'portal', tags: 'dev' })}
                    className="w-full border border-yellow-300 bg-white px-3 py-2 rounded hover:bg-yellow-100 text-sm text-left"
                  >
                    Run: vault log --type NOTE --tags dev
                  </button>
                </div>

                {/* Watch */}
                <div className="border-t border-yellow-200 pt-2 space-y-2">
                  <div className="text-[10px] font-bold text-yellow-700 uppercase">Watchdog Management</div>
                  <div className="grid grid-cols-2 gap-2">
                    <select
                      value={watchType}
                      onChange={(e) => setWatchType(e.target.value as any)}
                      className="p-2 border border-yellow-300 rounded text-xs bg-white"
                    >
                      <option value="url">URL</option>
                      <option value="query">Query</option>
                    </select>
                    <input
                      placeholder="Target (URL/Query)"
                      value={watchTarget}
                      onChange={(e) => setWatchTarget(e.target.value)}
                      className="p-2 border border-yellow-300 rounded text-xs bg-white"
                    />
                  </div>
                  <div className="grid grid-cols-2 gap-2">
                    <button
                      onClick={() => run('/vault/watch/add', { id: projectId, type: watchType, target: watchTarget, interval: watchInterval, tags: watchTags })}
                      disabled={!watchTarget.trim()}
                      className="w-full bg-yellow-600 text-white px-3 py-2 rounded hover:bg-yellow-700 text-sm disabled:opacity-50"
                    >
                      Run: vault watch add
                    </button>
                    <button
                      onClick={() => run('/vault/watch/list', { id: projectId })}
                      className="w-full border border-yellow-300 bg-white px-3 py-2 rounded hover:bg-yellow-100 text-sm"
                    >
                      Run: vault watch list
                    </button>
                  </div>
                </div>

                {/* Cache / Search set-result */}
                <div className="border-t border-yellow-200 pt-2 space-y-2">
                  <div className="text-[10px] font-bold text-yellow-700 uppercase">Cache Injection</div>
                  <input
                    placeholder="Query"
                    value={cacheQuery}
                    onChange={(e) => setCacheQuery(e.target.value)}
                    className="w-full p-2 border border-yellow-300 rounded text-xs bg-white"
                  />
                  <textarea
                    placeholder="Result JSON"
                    value={cacheSetJson}
                    onChange={(e) => setCacheSetJson(e.target.value)}
                    className="w-full p-2 border border-yellow-300 rounded text-xs font-mono h-20 bg-white"
                  />
                  <button
                    onClick={() => {
                      try {
                        const parsed = JSON.parse(cacheSetJson);
                        run('/vault/search', { query: cacheQuery, set_result: JSON.stringify(parsed) });
                      } catch (e) {
                        alert('Invalid JSON in result');
                      }
                    }}
                    disabled={!cacheQuery.trim()}
                    className="w-full bg-yellow-600 text-white px-3 py-2 rounded hover:bg-yellow-700 text-sm disabled:opacity-50"
                  >
                    Run: vault search --set-result
                  </button>
                </div>

                {/* Watchdog Once */}
                <div className="border-t border-yellow-200 pt-2">
                  <button
                    onClick={() => run('/vault/watchdog/once', { id: projectId, limit: 5, dry_run: true })}
                    className="w-full border border-yellow-300 bg-white px-3 py-2 rounded hover:bg-yellow-100 text-sm text-left"
                  >
                    Run: vault watchdog --once --dry-run
                  </button>
                </div>
              </div>
            )}
          </div>
        )}

        {tab === 'insights' && (
          <InsightsPanel projectId={projectId} run={run} />
        )}

        {tab === 'verification' && (
          <div className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-3 gap-2">
              <button
                onClick={() => run('/vault/verify/plan', { id: projectId })}
                className="border border-gray-300 bg-white px-3 py-2 rounded hover:bg-gray-50 text-sm flex items-center justify-center gap-2"
              >
                <Play className="w-4 h-4" /> plan
              </button>
              <button
                onClick={() => run('/vault/verify/list', { id: projectId, limit: 50 })}
                className="border border-gray-300 bg-white px-3 py-2 rounded hover:bg-gray-50 text-sm"
              >
                list
              </button>
              <button
                onClick={() => run('/vault/verify/run', { id: projectId, status: 'open', limit: 5 })}
                className="border border-gray-300 bg-white px-3 py-2 rounded hover:bg-gray-50 text-sm"
              >
                run
              </button>
            </div>
          </div>
        )}

        {tab === 'branches' && (
          <BranchesPanel projectId={projectId} run={run} />
        )}
      </div>
    </div>
  );
}

function InsightsPanel({
  projectId,
  run,
}: {
  projectId: string;
  run: (endpoint: string, payload?: unknown) => Promise<void>;
}) {
  const [title, setTitle] = useState('');
  const [content, setContent] = useState('');

  return (
    <div className="space-y-4">
      <div className="bg-white border border-gray-200 p-4 rounded shadow-sm">
        <div className="font-bold text-gray-800 mb-3">Add Insight</div>
        <input
          value={title}
          onChange={(e) => setTitle(e.target.value)}
          className="w-full p-2 border border-gray-300 rounded text-sm mb-2"
          placeholder="Title"
        />
        <textarea
          value={content}
          onChange={(e) => setContent(e.target.value)}
          className="w-full p-2 border border-gray-300 rounded text-sm h-24 mb-3"
          placeholder="Content"
        />
        <div className="flex justify-end">
          <button
            disabled={!title.trim() || !content.trim()}
            onClick={async () => {
              await run('/vault/insight/add', { id: projectId, title, content, tags: '' });
              setTitle('');
              setContent('');
            }}
            className="bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700 disabled:opacity-50 text-sm"
          >
            Add
          </button>
        </div>
      </div>

      <button
        onClick={() => run('/vault/insight/list', { id: projectId })}
        className="border border-gray-300 bg-white px-4 py-2 rounded hover:bg-gray-50 text-sm"
      >
        Run: vault insight (list)
      </button>
    </div>
  );
}

function BranchesPanel({
  projectId,
  run,
}: {
  projectId: string;
  run: (endpoint: string, payload?: unknown) => Promise<void>;
}) {
  const [name, setName] = useState('');

  return (
    <div className="space-y-4">
      <div className="bg-white border border-gray-200 p-4 rounded shadow-sm">
        <div className="font-bold text-gray-800 mb-3">Create Branch</div>
        <div className="flex gap-2">
          <input
            value={name}
            onChange={(e) => setName(e.target.value)}
            className="flex-1 p-2 border border-gray-300 rounded text-sm"
            placeholder="Branch name"
          />
          <button
            disabled={!name.trim()}
            onClick={async () => {
              await run('/vault/branch/create', { id: projectId, name });
              setName('');
            }}
            className="bg-gray-900 text-white px-4 py-2 rounded hover:bg-gray-800 disabled:opacity-50 text-sm"
          >
            Create
          </button>
        </div>
      </div>

      <button
        onClick={() => run('/vault/branch/list', { id: projectId })}
        className="border border-gray-300 bg-white px-4 py-2 rounded hover:bg-gray-50 text-sm"
      >
        Run: vault branch list
      </button>
    </div>
  );
}

function MainApp() {
  const [authed, setAuthed] = useState(false);
  const [token, setToken] = useState('');
  const [authError, setAuthError] = useState<string | null>(null);

  const [devMode, setDevMode] = useState(false);

  const [currentProject, setCurrentProject] = useState<string | null>(null);
  const [lastResult, setLastResult] = useState<VaultRunResult | null>(null);

  useEffect(() => {
    apiJson('/auth/status', { method: 'GET' })
      .then(() => setAuthed(true))
      .catch(() => setAuthed(false));
  }, []);

  async function handleLogin() {
    setAuthError(null);
    try {
      await apiJson('/auth/login', { method: 'POST', body: JSON.stringify({ token }) });
      setToken('');
      setAuthed(true);
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : String(e);
      setAuthError(msg);
      setAuthed(false);
    }
  }

  async function handleLogout() {
    try {
      await apiJson('/auth/logout', { method: 'POST', body: '{}' });
    } finally {
      setAuthed(false);
      setCurrentProject(null);
      setLastResult(null);
    }
  }

  if (!authed) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-100 p-4 font-mono">
        <div className="bg-white p-8 rounded shadow border max-w-sm w-full space-y-4">
          <h1 className="text-xl font-bold">ResearchVault Portal — Login</h1>
          <div className="text-sm text-gray-600">
            Enter your <code>RESEARCHVAULT_PORTAL_TOKEN</code>. The token is never placed in URLs.
          </div>
          <input
            type="password"
            value={token}
            onChange={(e) => setToken(e.target.value)}
            className="w-full border p-2 rounded text-gray-900 bg-white"
            placeholder="Token"
          />
          <button
            onClick={handleLogin}
            disabled={!token.trim()}
            className="w-full bg-black text-white p-2 rounded disabled:opacity-50"
          >
            Login
          </button>
          {authError && <div className="text-sm text-red-700">{authError}</div>}
        </div>
      </div>
    );
  }

  return (
    <div className={`min-h-screen bg-gray-50 text-gray-900 font-sans flex flex-col ${devMode ? 'border-4 border-yellow-400' : ''}`}>
      {devMode && (
        <div className="bg-yellow-400 text-yellow-900 px-4 py-1 text-center text-xs font-bold uppercase tracking-wider">
          <AlertTriangle className="inline w-3 h-3 mr-1" /> Advanced / Developer Mode Active
        </div>
      )}

      <header className="bg-white border-b border-gray-200 px-6 py-3 flex justify-between items-center sticky top-0 z-10">
        <div className="flex items-center gap-3">
          <Terminal className="w-6 h-6 text-gray-700" />
          <div>
            <div className="font-bold text-lg tracking-tight">Portal Command Center</div>
            <div className="text-xs text-gray-500">
              A visual shell over <code>scripts.vault</code>. Every button runs exactly one CLI command.
            </div>
          </div>
        </div>

        <div className="flex items-center gap-3">
          <button
            onClick={() => setDevMode((v) => !v)}
            className={`text-xs px-2 py-1 rounded border ${
              devMode
                ? 'bg-yellow-100 border-yellow-400 text-yellow-800'
                : 'bg-gray-100 border-gray-300 text-gray-600'
            }`}
          >
            {devMode ? 'Dev Mode ON' : 'Dev Mode OFF'}
          </button>
          <button onClick={handleLogout} className="text-sm text-gray-500 hover:text-red-600">
            Logout
          </button>
        </div>
      </header>

      <main className="flex-1 p-6 max-w-6xl mx-auto w-full grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2">
          {!currentProject ? (
            <EntryScreen onSelectProject={setCurrentProject} setLastResult={setLastResult} />
          ) : (
            <ProjectDetail
              projectId={currentProject}
              onBack={() => setCurrentProject(null)}
              setLastResult={setLastResult}
              devMode={devMode}
            />
          )}
        </div>

        <div className="lg:col-span-1">
          <div className="sticky top-20">
            <div className="flex items-center gap-2 mb-2 text-gray-600 font-mono text-xs uppercase tracking-wider">
              <Terminal className="w-3 h-3" /> Last Command Output
            </div>
            <CommandOutput result={lastResult} />
          </div>
        </div>
      </main>
    </div>
  );
}

export default function App() {
  return <MainApp />;
}
