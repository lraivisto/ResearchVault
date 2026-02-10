import { useEffect, useMemo, useState } from 'react';
import { AlertTriangle, CheckCircle2, RefreshCw, XCircle } from 'lucide-react';

import type { DiagnosticsResponse, DiagnosticsHint, SecretsStatusResponse } from '@/lib/api';
import { systemGet, systemPost } from '@/lib/api';

function HintCard({
  hint,
  onApplyDb,
}: {
  hint: DiagnosticsHint;
  onApplyDb: (path: string) => void;
}) {
  const isHigh = hint.severity === 'high';
  return (
    <div className={`border rounded p-4 ${isHigh ? 'border-red-500/40 bg-red-500/10' : 'border-white/10 bg-void-surface'}`}>
      <div className="flex items-start gap-3">
        <AlertTriangle className={`h-5 w-5 mt-0.5 ${isHigh ? 'text-red-300' : 'text-amber'}`} />
        <div className="flex-1">
          <div className="font-semibold text-gray-100">{hint.title}</div>
          <div className="text-sm text-gray-300 mt-1">{hint.detail}</div>
          {typeof hint.recommend_db_path === 'string' && hint.recommend_db_path && (
            <div className="mt-3 flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
              <div className="text-xs font-mono text-gray-400 break-all">{hint.recommend_db_path}</div>
              <button
                type="button"
                onClick={() => onApplyDb(hint.recommend_db_path as string)}
                className="text-xs font-mono px-3 py-1.5 rounded border border-cyan text-cyan bg-cyan-dim hover:border-cyan/80"
              >
                Switch DB
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

export default function DiagnosticsPanel({
  refreshKey,
  onApplyDb,
}: {
  refreshKey: number;
  onApplyDb: (path: string) => Promise<void> | void;
}) {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [diag, setDiag] = useState<DiagnosticsResponse | null>(null);
  const [braveKey, setBraveKey] = useState('');
  const [savingBrave, setSavingBrave] = useState(false);

  async function refresh() {
    setLoading(true);
    setError(null);
    try {
      const data = await systemGet<DiagnosticsResponse>('/diagnostics');
      setDiag(data);
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    refresh();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [refreshKey]);

  const cliOk = diag?.cli.ok ?? false;
  const hints = diag?.hints ?? [];

  const statusBadge = useMemo(() => {
    if (!diag) return null;
    if (cliOk && hints.length === 0) {
      return (
        <div className="flex items-center gap-2 text-green-300 text-sm font-mono">
          <CheckCircle2 className="h-4 w-4" />
          <span>healthy</span>
        </div>
      );
    }
    return (
      <div className="flex items-center gap-2 text-amber text-sm font-mono">
        <AlertTriangle className="h-4 w-4" />
        <span>needs attention</span>
      </div>
    );
  }, [cliOk, diag, hints.length]);

  async function saveBrave() {
    if (!braveKey.trim()) return;
    setSavingBrave(true);
    setError(null);
    try {
      await systemPost<SecretsStatusResponse>('/secrets/brave', { api_key: braveKey.trim() });
      setBraveKey('');
      await refresh();
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setSavingBrave(false);
    }
  }

  async function clearBrave() {
    setSavingBrave(true);
    setError(null);
    try {
      await systemPost<SecretsStatusResponse>('/secrets/brave/clear', {});
      await refresh();
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setSavingBrave(false);
    }
  }

  return (
    <div className="space-y-4">
      <div className="bg-void-surface border border-white/10 rounded-lg p-4">
        <div className="flex items-start justify-between gap-3">
          <div>
            <div className="text-xs uppercase tracking-wider text-gray-400 font-mono">Diagnostics</div>
            <div className="text-lg font-semibold text-gray-100">Backend, CLI, DB handshake</div>
            <div className="text-sm text-gray-400 mt-1">
              If data is missing, this panel should tell you exactly which DB is active and what to do next.
            </div>
          </div>
          <div className="flex items-center gap-3">
            {statusBadge}
            <button
              type="button"
              onClick={refresh}
              className="text-xs font-mono px-3 py-1.5 rounded border border-white/10 text-gray-300 hover:text-white hover:border-white/20"
              disabled={loading}
            >
              <RefreshCw className={`inline h-3.5 w-3.5 mr-1 ${loading ? 'animate-spin' : ''}`} />
              Refresh
            </button>
          </div>
        </div>
      </div>

      {error && (
        <div className="border border-red-500/40 bg-red-500/10 rounded p-4 text-sm text-red-200 font-mono">
          {error}
        </div>
      )}

      {diag && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
          <div className="bg-void-surface border border-white/10 rounded-lg p-4">
            <div className="text-xs uppercase tracking-wider text-gray-400 font-mono mb-2">Current DB</div>
            <div className="text-sm text-gray-200 font-mono break-all">{diag.db.current.path}</div>
            <div className="text-xs text-gray-400 mt-2 font-mono">
              src:{diag.db.current.source} | schema:{diag.db.current.schema_version ?? 'n/a'} | projects:
              {diag.db.current.counts?.projects ?? 'n/a'} | findings:{diag.db.current.counts?.findings ?? 'n/a'}
            </div>
            <div className="text-xs text-gray-500 mt-1">{diag.db.current.note}</div>
          </div>

          <div className="bg-void-surface border border-white/10 rounded-lg p-4">
            <div className="text-xs uppercase tracking-wider text-gray-400 font-mono mb-2">CLI Probe</div>
            <div className="flex items-center gap-2 text-sm font-mono">
              {diag.cli.ok ? (
                <>
                  <CheckCircle2 className="h-4 w-4 text-green-300" />
                  <span className="text-green-200">vault list ok</span>
                  <span className="text-gray-500">(projects:{diag.cli.projects_parsed ?? 'n/a'})</span>
                </>
              ) : (
                <>
                  <XCircle className="h-4 w-4 text-red-300" />
                  <span className="text-red-200">vault list failed</span>
                  <span className="text-gray-500">(exit {diag.cli.exit_code})</span>
                </>
              )}
            </div>
            {diag.cli.stderr && (
              <pre className="mt-3 text-xs text-red-200/90 bg-void border border-white/10 rounded p-3 overflow-auto max-h-40 whitespace-pre-wrap">
                {diag.cli.stderr}
              </pre>
            )}
            {diag.cli.parse_error && (
              <div className="mt-2 text-xs text-amber font-mono">parse_error: {diag.cli.parse_error}</div>
            )}
          </div>
        </div>
      )}

      {diag && (
        <div className="bg-void-surface border border-white/10 rounded-lg p-4">
          <div className="flex items-start justify-between gap-3">
            <div>
              <div className="text-xs uppercase tracking-wider text-gray-400 font-mono">Search Provider</div>
              <div className="text-lg font-semibold text-gray-100">Brave Search</div>
              <div className="text-sm text-gray-400 mt-1">
                Live search, verification missions, and watchdog query targets require a Brave API key.
              </div>
            </div>
            <div className="text-xs font-mono text-gray-400">
              {diag.providers.brave.configured ? (
                <span className="text-green-300">configured</span>
              ) : (
                <span className="text-amber">not configured</span>
              )}{' '}
              <span className="text-gray-600">|</span> src:{diag.providers.brave.source}
            </div>
          </div>

          <div className="mt-4 flex flex-col gap-2 sm:flex-row sm:items-center">
            <input
              type="password"
              value={braveKey}
              onChange={(e) => setBraveKey(e.target.value)}
              placeholder="Paste BRAVE_API_KEY"
              className="flex-1 bg-void border border-white/10 rounded px-3 py-2 text-sm text-gray-100 font-mono placeholder:text-gray-600"
            />
            <div className="flex items-center gap-2">
              <button
                type="button"
                onClick={saveBrave}
                disabled={savingBrave || !braveKey.trim()}
                className="text-xs font-mono px-3 py-2 rounded border border-cyan text-cyan bg-cyan-dim disabled:opacity-50"
              >
                Save Key
              </button>
              <button
                type="button"
                onClick={clearBrave}
                disabled={savingBrave}
                className="text-xs font-mono px-3 py-2 rounded border border-white/10 text-gray-300 hover:text-white hover:border-white/20 disabled:opacity-50"
              >
                Clear
              </button>
            </div>
          </div>

          <div className="mt-2 text-[11px] text-gray-500 font-mono">
            Stored locally in <span className="text-gray-400">~/.researchvault/portal/secrets.json</span> and injected into vault commands.
          </div>
        </div>
      )}

      {hints.length > 0 && (
        <div className="space-y-3">
          <div className="text-xs uppercase tracking-wider text-gray-400 font-mono">Actionable Hints</div>
          {hints.map((h, idx) => (
            <HintCard
              key={`${h.type}-${idx}`}
              hint={h}
              onApplyDb={async (path) => {
                await onApplyDb(path);
                await refresh();
              }}
            />
          ))}
        </div>
      )}

      {diag && (
        <div className="bg-void-surface border border-white/10 rounded-lg p-4">
          <div className="text-xs uppercase tracking-wider text-gray-400 font-mono mb-2">Vault DBs Seen</div>
          <div className="space-y-2">
            {diag.db.candidates.map((c) => (
              <div key={c.path} className="flex items-center justify-between gap-3 border border-white/10 rounded px-3 py-2">
                <div className="min-w-0">
                  <div className="text-xs font-mono text-gray-200 break-all">{c.path}</div>
                  <div className="text-[11px] font-mono text-gray-500">
                    {c.exists ? 'exists' : 'missing'} | projects:{c.counts?.projects ?? 'n/a'} findings:{c.counts?.findings ?? 'n/a'}{' '}
                    {c.error ? `| error:${c.error}` : ''}
                  </div>
                </div>
                {c.path !== diag.db.current.path && (
                  <button
                    type="button"
                    onClick={async () => {
                      await onApplyDb(c.path);
                      await refresh();
                    }}
                    className="text-xs font-mono px-3 py-1.5 rounded border border-white/10 text-gray-300 hover:text-white hover:border-white/20"
                  >
                    Use
                  </button>
                )}
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
