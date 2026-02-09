import { useEffect, useMemo, useState } from 'react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { API_BASE } from './config';

const queryClient = new QueryClient();

type VaultRunResult = {
  argv: string[];
  exit_code: number;
  stdout: string;
  stderr: string;
  truncated: boolean;
  ok: boolean;
};

type RunRecord = VaultRunResult & { at: string; endpoint: string };

async function apiJson<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    ...init,
    credentials: 'include',
    headers: {
      'Content-Type': 'application/json',
      ...(init?.headers || {}),
    },
  });

  if (!res.ok) {
    const text = await res.text();
    throw new Error(`${res.status}: ${text}`);
  }
  return res.json();
}

function Section({ title, children }: { title: string; children: any }) {
  return (
    <section className="border border-gray-300 bg-white">
      <div className="border-b border-gray-200 px-4 py-2 font-bold">{title}</div>
      <div className="p-4">{children}</div>
    </section>
  );
}

function AppContent() {
  const [authed, setAuthed] = useState(false);
  const [token, setToken] = useState('');
  const [authError, setAuthError] = useState<string | null>(null);

  const [history, setHistory] = useState<RunRecord[]>([]);

  const last = useMemo(() => history[0], [history]);

  // ---- command form state (boring, explicit, literal) ----
  const [projectId, setProjectId] = useState('');

  // init
  const [initName, setInitName] = useState('');
  const [initObjective, setInitObjective] = useState('');
  const [initPriority, setInitPriority] = useState(0);

  // update
  const [updateStatus, setUpdateStatus] = useState('');
  const [updatePriority, setUpdatePriority] = useState<string>('');

  // search
  const [searchQuery, setSearchQuery] = useState('');
  const [searchSetResultJson, setSearchSetResultJson] = useState('');

  // scuttle
  const [scuttleUrl, setScuttleUrl] = useState('');
  const [scuttleTags, setScuttleTags] = useState('');
  const [scuttleBranch, setScuttleBranch] = useState('');

  // log
  const [logType, setLogType] = useState('NOTE');
  const [logStep, setLogStep] = useState(0);
  const [logPayloadJson, setLogPayloadJson] = useState('{}');
  const [logConf, setLogConf] = useState(1.0);
  const [logSource, setLogSource] = useState('portal');
  const [logTags, setLogTags] = useState('');
  const [logBranch, setLogBranch] = useState('');

  // status
  const [statusFilterTag, setStatusFilterTag] = useState('');
  const [statusBranch, setStatusBranch] = useState('');

  // insight
  const [insTitle, setInsTitle] = useState('');
  const [insContent, setInsContent] = useState('');
  const [insUrl, setInsUrl] = useState('');
  const [insTags, setInsTags] = useState('');
  const [insConf, setInsConf] = useState(1.0);
  const [insBranch, setInsBranch] = useState('');
  const [insFilterTag, setInsFilterTag] = useState('');

  // export
  const [exportFormat, setExportFormat] = useState<'json' | 'markdown'>('json');
  const [exportBranch, setExportBranch] = useState('');

  // verify
  const [verifyThreshold, setVerifyThreshold] = useState(0.7);
  const [verifyMax, setVerifyMax] = useState(20);
  const [verifyBranch, setVerifyBranch] = useState('');
  const [verifyListStatus, setVerifyListStatus] = useState('');
  const [verifyListLimit, setVerifyListLimit] = useState(50);
  const [verifyRunStatus, setVerifyRunStatus] = useState<'open' | 'blocked'>('open');
  const [verifyRunLimit, setVerifyRunLimit] = useState(5);
  const [verifyCompleteMission, setVerifyCompleteMission] = useState('');
  const [verifyCompleteStatus, setVerifyCompleteStatus] = useState<'done' | 'cancelled' | 'open'>('done');
  const [verifyCompleteNote, setVerifyCompleteNote] = useState('');

  // synthesize
  const [synThreshold, setSynThreshold] = useState(0.78);
  const [synTopK, setSynTopK] = useState(5);
  const [synMaxLinks, setSynMaxLinks] = useState(50);
  const [synDryRun, setSynDryRun] = useState(false);
  const [synBranch, setSynBranch] = useState('');

  // strategy
  const [stratBranch, setStratBranch] = useState('');
  const [stratExecute, setStratExecute] = useState(false);
  const [stratFormat, setStratFormat] = useState<'rich' | 'json'>('rich');

  // watch
  const [watchType, setWatchType] = useState<'url' | 'query'>('url');
  const [watchTarget, setWatchTarget] = useState('');
  const [watchInterval, setWatchInterval] = useState(3600);
  const [watchTags, setWatchTags] = useState('');
  const [watchBranch, setWatchBranch] = useState('');
  const [watchListStatus, setWatchListStatus] = useState<'active' | 'disabled' | 'all'>('active');
  const [watchDisableId, setWatchDisableId] = useState('');

  // watchdog
  const [wdLimit, setWdLimit] = useState(10);
  const [wdDryRun, setWdDryRun] = useState(false);
  const [wdBranch, setWdBranch] = useState('');

  // branches/hypotheses/artifacts
  const [branchName, setBranchName] = useState('');
  const [branchFrom, setBranchFrom] = useState('');
  const [branchHypothesis, setBranchHypothesis] = useState('');

  const [hypBranch, setHypBranch] = useState('main');
  const [hypStatement, setHypStatement] = useState('');
  const [hypRationale, setHypRationale] = useState('');
  const [hypConf, setHypConf] = useState(0.5);
  const [hypStatus, setHypStatus] = useState<'open' | 'accepted' | 'rejected' | 'archived'>('open');
  const [hypListBranch, setHypListBranch] = useState('');

  const [artPath, setArtPath] = useState('');
  const [artType, setArtType] = useState('FILE');
  const [artMetadataJson, setArtMetadataJson] = useState('{}');
  const [artBranch, setArtBranch] = useState('');
  const [artListBranch, setArtListBranch] = useState('');

  async function run(endpoint: string, payload?: any, method: 'GET' | 'POST' = 'POST') {
    const at = new Date().toISOString();
    const res: VaultRunResult = method === 'GET'
      ? await apiJson(endpoint, { method: 'GET' })
      : await apiJson(endpoint, { method: 'POST', body: JSON.stringify(payload || {}) });

    setHistory((prev) => [{ ...res, at, endpoint }, ...prev].slice(0, 50));
  }

  useEffect(() => {
    // Attempt cookie-based auth on load.
    apiJson('/auth/status', { method: 'GET' })
      .then(() => setAuthed(true))
      .catch(() => setAuthed(false));
  }, []);

  async function handleLogin() {
    setAuthError(null);
    try {
      await apiJson('/auth/login', { method: 'POST', body: JSON.stringify({ token }) });
      setToken(''); // do not keep secrets around
      setAuthed(true);
    } catch (e: any) {
      setAuthed(false);
      setAuthError(e?.message || 'Login failed');
    }
  }

  async function handleLogout() {
    try {
      await apiJson('/auth/logout', { method: 'POST', body: '{}' });
    } finally {
      setAuthed(false);
      setHistory([]);
    }
  }

  if (!authed) {
    return (
      <div className="min-h-screen bg-gray-100 text-gray-900 font-mono p-6">
        <div className="max-w-lg mx-auto border border-gray-300 bg-white">
          <div className="border-b border-gray-200 px-4 py-2 font-bold">ResearchVault Portal — Login</div>
          <div className="p-4 space-y-3">
            <div className="text-sm text-gray-700">
              Enter your <code>RESEARCHVAULT_PORTAL_TOKEN</code>. The token is never placed in URLs.
            </div>
            <input
              className="w-full border border-gray-300 p-2"
              type="password"
              placeholder="Portal token"
              value={token}
              onChange={(e) => setToken(e.target.value)}
            />
            <button className="border border-gray-400 bg-gray-200 px-4 py-2" onClick={handleLogin}>
              Login
            </button>
            {authError && <div className="text-sm text-red-700">{authError}</div>}
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-100 text-gray-900 font-mono p-6">
      <header className="mb-4 flex items-end justify-between">
        <div>
          <div className="text-2xl font-bold">ResearchVault Portal</div>
          <div className="text-sm text-gray-600">A visual shell over <code>scripts.vault</code>. Every button runs exactly one CLI command.</div>
        </div>
        <button className="border border-gray-400 bg-gray-200 px-3 py-1" onClick={handleLogout}>
          Logout
        </button>
      </header>

      <div className="mb-4 border border-gray-300 bg-white p-4 flex gap-4 items-end">
        <div className="flex-1">
          <label className="block text-xs font-bold text-gray-700 mb-1">Project ID</label>
          <input className="w-full border border-gray-300 p-2" value={projectId} onChange={(e) => setProjectId(e.target.value)} placeholder="e.g. metal-v1" />
        </div>
        <button className="border border-gray-400 bg-gray-200 px-3 py-2" onClick={() => run('/vault/list', undefined, 'GET')}>vault list</button>
        <button className="border border-gray-400 bg-gray-200 px-3 py-2" onClick={() => run('/vault/status', { id: projectId })} disabled={!projectId}>vault status</button>
        <button className="border border-gray-400 bg-gray-200 px-3 py-2" onClick={() => run('/vault/summary', { id: projectId })} disabled={!projectId}>vault summary</button>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <Section title="init (create project)">
          <div className="grid grid-cols-1 gap-2">
            <input className="border border-gray-300 p-2" placeholder="name (optional)" value={initName} onChange={(e) => setInitName(e.target.value)} />
            <textarea className="border border-gray-300 p-2" placeholder="objective" value={initObjective} onChange={(e) => setInitObjective(e.target.value)} />
            <input className="border border-gray-300 p-2" type="number" placeholder="priority" value={initPriority} onChange={(e) => setInitPriority(parseInt(e.target.value || '0', 10))} />
            <button className="border border-gray-400 bg-gray-200 px-3 py-2" disabled={!projectId || !initObjective} onClick={() => run('/vault/init', { id: projectId, name: initName || null, objective: initObjective, priority: initPriority })}>
              Run: vault init
            </button>
          </div>
        </Section>

        <Section title="update (status / priority)">
          <div className="grid grid-cols-1 gap-2">
            <select className="border border-gray-300 p-2" value={updateStatus} onChange={(e) => setUpdateStatus(e.target.value)}>
              <option value="">(no status change)</option>
              <option value="active">active</option>
              <option value="paused">paused</option>
              <option value="completed">completed</option>
              <option value="failed">failed</option>
            </select>
            <input className="border border-gray-300 p-2" placeholder="priority (optional)" value={updatePriority} onChange={(e) => setUpdatePriority(e.target.value)} />
            <button className="border border-gray-400 bg-gray-200 px-3 py-2" disabled={!projectId || (!updateStatus && updatePriority === '')} onClick={() => run('/vault/update', { id: projectId, status: updateStatus || null, priority: updatePriority === '' ? null : parseInt(updatePriority, 10) })}>
              Run: vault update
            </button>
          </div>
        </Section>

        <Section title="search (cache + Brave API)">
          <div className="grid grid-cols-1 gap-2">
            <input className="border border-gray-300 p-2" placeholder="query" value={searchQuery} onChange={(e) => setSearchQuery(e.target.value)} />
            <textarea className="border border-gray-300 p-2 h-24" placeholder="optional: set-result JSON (manual injection)" value={searchSetResultJson} onChange={(e) => setSearchSetResultJson(e.target.value)} />
            <button className="border border-gray-400 bg-gray-200 px-3 py-2" disabled={!searchQuery} onClick={() => {
              let set_result = null;
              try {
                if (searchSetResultJson.trim()) {
                  set_result = JSON.parse(searchSetResultJson);
                }
                run('/vault/search', { query: searchQuery, set_result });
              } catch (e) {
                alert('Invalid JSON in set-result');
              }
            }}>
              Run: vault search
            </button>
          </div>
        </Section>

        <Section title="scuttle (ingest)">
          <div className="grid grid-cols-1 gap-2">
            <input className="border border-gray-300 p-2" placeholder="url" value={scuttleUrl} onChange={(e) => setScuttleUrl(e.target.value)} />
            <input className="border border-gray-300 p-2" placeholder="tags (comma-separated)" value={scuttleTags} onChange={(e) => setScuttleTags(e.target.value)} />
            <input className="border border-gray-300 p-2" placeholder="branch (optional)" value={scuttleBranch} onChange={(e) => setScuttleBranch(e.target.value)} />
            <button className="border border-gray-400 bg-gray-200 px-3 py-2" disabled={!projectId || !scuttleUrl} onClick={() => run('/vault/scuttle', { id: projectId, url: scuttleUrl, tags: scuttleTags, branch: scuttleBranch || null })}>
              Run: vault scuttle
            </button>
          </div>
        </Section>

        <Section title="log (event)">
          <div className="grid grid-cols-1 gap-2">
            <input className="border border-gray-300 p-2" placeholder="type" value={logType} onChange={(e) => setLogType(e.target.value)} />
            <input className="border border-gray-300 p-2" type="number" placeholder="step" value={logStep} onChange={(e) => setLogStep(parseInt(e.target.value || '0', 10))} />
            <textarea className="border border-gray-300 p-2 h-24" placeholder="payload JSON" value={logPayloadJson} onChange={(e) => setLogPayloadJson(e.target.value)} />
            <div className="grid grid-cols-2 gap-2">
              <input className="border border-gray-300 p-2" type="number" step="0.01" min="0" max="1" placeholder="conf" value={logConf} onChange={(e) => setLogConf(parseFloat(e.target.value || '1'))} />
              <input className="border border-gray-300 p-2" placeholder="source" value={logSource} onChange={(e) => setLogSource(e.target.value)} />
            </div>
            <div className="grid grid-cols-2 gap-2">
              <input className="border border-gray-300 p-2" placeholder="tags" value={logTags} onChange={(e) => setLogTags(e.target.value)} />
              <input className="border border-gray-300 p-2" placeholder="branch (optional)" value={logBranch} onChange={(e) => setLogBranch(e.target.value)} />
            </div>
            <button className="border border-gray-400 bg-gray-200 px-3 py-2" disabled={!projectId} onClick={() => {
              try {
                run('/vault/log', {
                  id: projectId,
                  type: logType,
                  step: logStep,
                  payload: JSON.parse(logPayloadJson || '{}'),
                  conf: logConf,
                  source: logSource,
                  tags: logTags,
                  branch: logBranch || null,
                });
              } catch (e) {
                alert('Invalid JSON in payload');
              }
            }}>
              Run: vault log
            </button>
          </div>
        </Section>

        <Section title="status (detailed)">
          <div className="grid grid-cols-1 gap-2">
            <input className="border border-gray-300 p-2" placeholder="filter-tag (optional)" value={statusFilterTag} onChange={(e) => setStatusFilterTag(e.target.value)} />
            <input className="border border-gray-300 p-2" placeholder="branch (optional)" value={statusBranch} onChange={(e) => setStatusBranch(e.target.value)} />
            <button className="border border-gray-400 bg-gray-200 px-3 py-2" disabled={!projectId} onClick={() => run('/vault/status', { id: projectId, filter_tag: statusFilterTag || null, branch: statusBranch || null })}>
              Run: vault status
            </button>
          </div>
        </Section>

        <Section title="insight">
          <div className="grid grid-cols-1 gap-3">
            <div className="font-bold text-sm">Add</div>
            <input className="border border-gray-300 p-2" placeholder="title" value={insTitle} onChange={(e) => setInsTitle(e.target.value)} />
            <textarea className="border border-gray-300 p-2 h-20" placeholder="content" value={insContent} onChange={(e) => setInsContent(e.target.value)} />
            <input className="border border-gray-300 p-2" placeholder="url" value={insUrl} onChange={(e) => setInsUrl(e.target.value)} />
            <div className="grid grid-cols-2 gap-2">
              <input className="border border-gray-300 p-2" placeholder="tags" value={insTags} onChange={(e) => setInsTags(e.target.value)} />
              <input className="border border-gray-300 p-2" type="number" step="0.01" min="0" max="1" placeholder="conf" value={insConf} onChange={(e) => setInsConf(parseFloat(e.target.value || '1'))} />
            </div>
            <input className="border border-gray-300 p-2" placeholder="branch (optional)" value={insBranch} onChange={(e) => setInsBranch(e.target.value)} />
            <button className="border border-gray-400 bg-gray-200 px-3 py-2" disabled={!projectId || !insTitle || !insContent} onClick={() => run('/vault/insight/add', { id: projectId, title: insTitle, content: insContent, url: insUrl, tags: insTags, conf: insConf, branch: insBranch || null })}>
              Run: vault insight --add
            </button>

            <div className="font-bold text-sm pt-2 border-t border-gray-200">List</div>
            <input className="border border-gray-300 p-2" placeholder="filter-tag (optional)" value={insFilterTag} onChange={(e) => setInsFilterTag(e.target.value)} />
            <button className="border border-gray-400 bg-gray-200 px-3 py-2" disabled={!projectId} onClick={() => run('/vault/insight/list', { id: projectId, filter_tag: insFilterTag || null, branch: insBranch || null })}>
              Run: vault insight (list)
            </button>
          </div>
        </Section>

        <Section title="export">
          <div className="grid grid-cols-1 gap-2">
            <select className="border border-gray-300 p-2" value={exportFormat} onChange={(e) => setExportFormat(e.target.value as any)}>
              <option value="json">json</option>
              <option value="markdown">markdown</option>
            </select>
            <input className="border border-gray-300 p-2" placeholder="branch (optional)" value={exportBranch} onChange={(e) => setExportBranch(e.target.value)} />
            <button className="border border-gray-400 bg-gray-200 px-3 py-2" disabled={!projectId} onClick={() => run('/vault/export', { id: projectId, format: exportFormat, branch: exportBranch || null })}>
              Run: vault export
            </button>
          </div>
        </Section>

        <Section title="verify (missions)">
          <div className="grid grid-cols-1 gap-3">
            <div className="font-bold text-sm">plan</div>
            <div className="grid grid-cols-2 gap-2">
              <input className="border border-gray-300 p-2" type="number" step="0.01" min="0" max="1" value={verifyThreshold} onChange={(e) => setVerifyThreshold(parseFloat(e.target.value || '0.7'))} />
              <input className="border border-gray-300 p-2" type="number" value={verifyMax} onChange={(e) => setVerifyMax(parseInt(e.target.value || '20', 10))} />
            </div>
            <input className="border border-gray-300 p-2" placeholder="branch (optional)" value={verifyBranch} onChange={(e) => setVerifyBranch(e.target.value)} />
            <button className="border border-gray-400 bg-gray-200 px-3 py-2" disabled={!projectId} onClick={() => run('/vault/verify/plan', { id: projectId, threshold: verifyThreshold, max: verifyMax, branch: verifyBranch || null })}>
              Run: vault verify plan
            </button>

            <div className="font-bold text-sm pt-2 border-t border-gray-200">list</div>
            <div className="grid grid-cols-2 gap-2">
              <input className="border border-gray-300 p-2" placeholder="status (optional)" value={verifyListStatus} onChange={(e) => setVerifyListStatus(e.target.value)} />
              <input className="border border-gray-300 p-2" type="number" value={verifyListLimit} onChange={(e) => setVerifyListLimit(parseInt(e.target.value || '50', 10))} />
            </div>
            <button className="border border-gray-400 bg-gray-200 px-3 py-2" disabled={!projectId} onClick={() => run('/vault/verify/list', { id: projectId, status: verifyListStatus || null, limit: verifyListLimit, branch: verifyBranch || null })}>
              Run: vault verify list
            </button>

            <div className="font-bold text-sm pt-2 border-t border-gray-200">run</div>
            <div className="grid grid-cols-2 gap-2">
              <select className="border border-gray-300 p-2" value={verifyRunStatus} onChange={(e) => setVerifyRunStatus(e.target.value as any)}>
                <option value="open">open</option>
                <option value="blocked">blocked</option>
              </select>
              <input className="border border-gray-300 p-2" type="number" value={verifyRunLimit} onChange={(e) => setVerifyRunLimit(parseInt(e.target.value || '5', 10))} />
            </div>
            <button className="border border-gray-400 bg-gray-200 px-3 py-2" disabled={!projectId} onClick={() => run('/vault/verify/run', { id: projectId, status: verifyRunStatus, limit: verifyRunLimit, branch: verifyBranch || null })}>
              Run: vault verify run
            </button>

            <div className="font-bold text-sm pt-2 border-t border-gray-200">complete (manual)</div>
            <input className="border border-gray-300 p-2" placeholder="mission id" value={verifyCompleteMission} onChange={(e) => setVerifyCompleteMission(e.target.value)} />
            <select className="border border-gray-300 p-2" value={verifyCompleteStatus} onChange={(e) => setVerifyCompleteStatus(e.target.value as any)}>
              <option value="done">done</option>
              <option value="cancelled">cancelled</option>
              <option value="open">open</option>
            </select>
            <input className="border border-gray-300 p-2" placeholder="note" value={verifyCompleteNote} onChange={(e) => setVerifyCompleteNote(e.target.value)} />
            <button className="border border-gray-400 bg-gray-200 px-3 py-2" disabled={!verifyCompleteMission} onClick={() => run('/vault/verify/complete', { mission: verifyCompleteMission, status: verifyCompleteStatus, note: verifyCompleteNote })}>
              Run: vault verify complete
            </button>
          </div>
        </Section>

        <Section title="synthesize">
          <div className="grid grid-cols-1 gap-2">
            <div className="grid grid-cols-3 gap-2">
              <input className="border border-gray-300 p-2" type="number" step="0.01" value={synThreshold} onChange={(e) => setSynThreshold(parseFloat(e.target.value || '0.78'))} />
              <input className="border border-gray-300 p-2" type="number" value={synTopK} onChange={(e) => setSynTopK(parseInt(e.target.value || '5', 10))} />
              <input className="border border-gray-300 p-2" type="number" value={synMaxLinks} onChange={(e) => setSynMaxLinks(parseInt(e.target.value || '50', 10))} />
            </div>
            <input className="border border-gray-300 p-2" placeholder="branch (optional)" value={synBranch} onChange={(e) => setSynBranch(e.target.value)} />
            <label className="text-sm"><input type="checkbox" checked={synDryRun} onChange={(e) => setSynDryRun(e.target.checked)} /> dry-run</label>
            <button className="border border-gray-400 bg-gray-200 px-3 py-2" disabled={!projectId} onClick={() => run('/vault/synthesize', { id: projectId, threshold: synThreshold, top_k: synTopK, max_links: synMaxLinks, dry_run: synDryRun, branch: synBranch || null })}>
              Run: vault synthesize
            </button>
          </div>
        </Section>

        <Section title="strategy">
          <div className="grid grid-cols-1 gap-2">
            <input className="border border-gray-300 p-2" placeholder="branch (optional)" value={stratBranch} onChange={(e) => setStratBranch(e.target.value)} />
            <select className="border border-gray-300 p-2" value={stratFormat} onChange={(e) => setStratFormat(e.target.value as any)}>
              <option value="rich">rich</option>
              <option value="json">json</option>
            </select>
            <label className="text-sm"><input type="checkbox" checked={stratExecute} onChange={(e) => setStratExecute(e.target.checked)} /> execute (safe subset)</label>
            <button className="border border-gray-400 bg-gray-200 px-3 py-2" disabled={!projectId} onClick={() => run('/vault/strategy', { id: projectId, branch: stratBranch || null, execute: stratExecute, format: stratFormat })}>
              Run: vault strategy
            </button>
          </div>
        </Section>

        <Section title="watch">
          <div className="grid grid-cols-1 gap-3">
            <div className="font-bold text-sm">add</div>
            <select className="border border-gray-300 p-2" value={watchType} onChange={(e) => setWatchType(e.target.value as any)}>
              <option value="url">url</option>
              <option value="query">query</option>
            </select>
            <input className="border border-gray-300 p-2" placeholder="target" value={watchTarget} onChange={(e) => setWatchTarget(e.target.value)} />
            <input className="border border-gray-300 p-2" type="number" value={watchInterval} onChange={(e) => setWatchInterval(parseInt(e.target.value || '3600', 10))} />
            <input className="border border-gray-300 p-2" placeholder="tags" value={watchTags} onChange={(e) => setWatchTags(e.target.value)} />
            <input className="border border-gray-300 p-2" placeholder="branch (optional)" value={watchBranch} onChange={(e) => setWatchBranch(e.target.value)} />
            <button className="border border-gray-400 bg-gray-200 px-3 py-2" disabled={!projectId || !watchTarget} onClick={() => run('/vault/watch/add', { id: projectId, type: watchType, target: watchTarget, interval: watchInterval, tags: watchTags, branch: watchBranch || null })}>
              Run: vault watch add
            </button>

            <div className="font-bold text-sm pt-2 border-t border-gray-200">list</div>
            <select className="border border-gray-300 p-2" value={watchListStatus} onChange={(e) => setWatchListStatus(e.target.value as any)}>
              <option value="active">active</option>
              <option value="disabled">disabled</option>
              <option value="all">all</option>
            </select>
            <button className="border border-gray-400 bg-gray-200 px-3 py-2" disabled={!projectId} onClick={() => run('/vault/watch/list', { id: projectId, status: watchListStatus, branch: watchBranch || null })}>
              Run: vault watch list
            </button>

            <div className="font-bold text-sm pt-2 border-t border-gray-200">disable</div>
            <input className="border border-gray-300 p-2" placeholder="target-id" value={watchDisableId} onChange={(e) => setWatchDisableId(e.target.value)} />
            <button className="border border-gray-400 bg-gray-200 px-3 py-2" disabled={!watchDisableId} onClick={() => run('/vault/watch/disable', { target_id: watchDisableId })}>
              Run: vault watch disable
            </button>
          </div>
        </Section>

        <Section title="watchdog (once)">
          <div className="grid grid-cols-1 gap-2">
            <input className="border border-gray-300 p-2" type="number" value={wdLimit} onChange={(e) => setWdLimit(parseInt(e.target.value || '10', 10))} />
            <input className="border border-gray-300 p-2" placeholder="branch (optional; requires project)" value={wdBranch} onChange={(e) => setWdBranch(e.target.value)} />
            <label className="text-sm"><input type="checkbox" checked={wdDryRun} onChange={(e) => setWdDryRun(e.target.checked)} /> dry-run</label>
            <button className="border border-gray-400 bg-gray-200 px-3 py-2" onClick={() => run('/vault/watchdog/once', { id: projectId || null, branch: wdBranch || null, limit: wdLimit, dry_run: wdDryRun })}>
              Run: vault watchdog --once
            </button>
          </div>
        </Section>

        <Section title="branch">
          <div className="grid grid-cols-1 gap-3">
            <div className="font-bold text-sm">create</div>
            <input className="border border-gray-300 p-2" placeholder="name" value={branchName} onChange={(e) => setBranchName(e.target.value)} />
            <input className="border border-gray-300 p-2" placeholder="from (optional parent branch name)" value={branchFrom} onChange={(e) => setBranchFrom(e.target.value)} />
            <input className="border border-gray-300 p-2" placeholder="hypothesis (optional)" value={branchHypothesis} onChange={(e) => setBranchHypothesis(e.target.value)} />
            <button className="border border-gray-400 bg-gray-200 px-3 py-2" disabled={!projectId || !branchName} onClick={() => run('/vault/branch/create', { id: projectId, name: branchName, from: branchFrom || null, hypothesis: branchHypothesis })}>
              Run: vault branch create
            </button>

            <div className="font-bold text-sm pt-2 border-t border-gray-200">list</div>
            <button className="border border-gray-400 bg-gray-200 px-3 py-2" disabled={!projectId} onClick={() => run('/vault/branch/list', { id: projectId })}>
              Run: vault branch list
            </button>
          </div>
        </Section>

        <Section title="hypothesis">
          <div className="grid grid-cols-1 gap-3">
            <div className="font-bold text-sm">add</div>
            <input className="border border-gray-300 p-2" placeholder="branch" value={hypBranch} onChange={(e) => setHypBranch(e.target.value)} />
            <input className="border border-gray-300 p-2" placeholder="statement" value={hypStatement} onChange={(e) => setHypStatement(e.target.value)} />
            <input className="border border-gray-300 p-2" placeholder="rationale" value={hypRationale} onChange={(e) => setHypRationale(e.target.value)} />
            <div className="grid grid-cols-2 gap-2">
              <input className="border border-gray-300 p-2" type="number" step="0.01" value={hypConf} onChange={(e) => setHypConf(parseFloat(e.target.value || '0.5'))} />
              <select className="border border-gray-300 p-2" value={hypStatus} onChange={(e) => setHypStatus(e.target.value as any)}>
                <option value="open">open</option>
                <option value="accepted">accepted</option>
                <option value="rejected">rejected</option>
                <option value="archived">archived</option>
              </select>
            </div>
            <button className="border border-gray-400 bg-gray-200 px-3 py-2" disabled={!projectId || !hypStatement} onClick={() => run('/vault/hypothesis/add', { id: projectId, branch: hypBranch, statement: hypStatement, rationale: hypRationale, conf: hypConf, status: hypStatus })}>
              Run: vault hypothesis add
            </button>

            <div className="font-bold text-sm pt-2 border-t border-gray-200">list</div>
            <input className="border border-gray-300 p-2" placeholder="branch (optional)" value={hypListBranch} onChange={(e) => setHypListBranch(e.target.value)} />
            <button className="border border-gray-400 bg-gray-200 px-3 py-2" disabled={!projectId} onClick={() => run('/vault/hypothesis/list', { id: projectId, branch: hypListBranch || null })}>
              Run: vault hypothesis list
            </button>
          </div>
        </Section>

        <Section title="artifact">
          <div className="grid grid-cols-1 gap-3">
            <div className="font-bold text-sm">add</div>
            <input className="border border-gray-300 p-2" placeholder="path" value={artPath} onChange={(e) => setArtPath(e.target.value)} />
            <input className="border border-gray-300 p-2" placeholder="type" value={artType} onChange={(e) => setArtType(e.target.value)} />
            <textarea className="border border-gray-300 p-2 h-20" placeholder="metadata JSON" value={artMetadataJson} onChange={(e) => setArtMetadataJson(e.target.value)} />
            <input className="border border-gray-300 p-2" placeholder="branch (optional)" value={artBranch} onChange={(e) => setArtBranch(e.target.value)} />
            <button className="border border-gray-400 bg-gray-200 px-3 py-2" disabled={!projectId || !artPath} onClick={() => {
              try {
                run('/vault/artifact/add', {
                  id: projectId,
                  path: artPath,
                  type: artType,
                  metadata: JSON.parse(artMetadataJson || '{}'),
                  branch: artBranch || null,
                });
              } catch (e) {
                alert('Invalid JSON in metadata');
              }
            }}>
              Run: vault artifact add
            </button>

            <div className="font-bold text-sm pt-2 border-t border-gray-200">list</div>
            <input className="border border-gray-300 p-2" placeholder="branch (optional)" value={artListBranch} onChange={(e) => setArtListBranch(e.target.value)} />
            <button className="border border-gray-400 bg-gray-200 px-3 py-2" disabled={!projectId} onClick={() => run('/vault/artifact/list', { id: projectId, branch: artListBranch || null })}>
              Run: vault artifact list
            </button>
          </div>
        </Section>
      </div>

      <div className="mt-4 grid grid-cols-1 lg:grid-cols-2 gap-4">
        <Section title="Last command output">
          {!last ? (
            <div className="text-gray-600">No commands executed yet.</div>
          ) : (
            <div className="space-y-2">
              <div className="text-xs text-gray-600">{last.at}</div>
              <div className="text-xs"><span className="font-bold">argv:</span> {last.argv.join(' ')}</div>
              <div className="text-xs"><span className="font-bold">exit:</span> {last.exit_code} {last.truncated ? '(truncated)' : ''}</div>
              {last.stderr && (
                <pre className="text-xs bg-red-50 border border-red-200 p-2 overflow-auto whitespace-pre-wrap">{last.stderr}</pre>
              )}
              <pre className="text-xs bg-gray-50 border border-gray-200 p-2 overflow-auto whitespace-pre-wrap">{last.stdout}</pre>
            </div>
          )}
        </Section>

        <Section title="Run history (most recent first)">
          <div className="text-xs text-gray-600 mb-2">Stored in-memory (50 max). Reload clears it.</div>
          <div className="max-h-[420px] overflow-auto">
            <table className="w-full text-xs border-collapse">
              <thead>
                <tr className="text-left border-b border-gray-200">
                  <th className="p-1">time</th>
                  <th className="p-1">exit</th>
                  <th className="p-1">command</th>
                </tr>
              </thead>
              <tbody>
                {history.map((h, idx) => (
                  <tr key={idx} className="border-b border-gray-100">
                    <td className="p-1 text-gray-600">{h.at}</td>
                    <td className={`p-1 ${h.ok ? 'text-green-700' : 'text-red-700'}`}>{h.exit_code}</td>
                    <td className="p-1">{h.argv.slice(3).join(' ')}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </Section>
      </div>

      <div className="mt-4 text-xs text-gray-600">
        Not exposed in Portal: <code>vault mcp</code> (long-running server; use CLI).
      </div>
    </div>
  );
}

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <AppContent />
    </QueryClientProvider>
  );
}
