import json
import sqlite3
import hashlib
import os
import re
import uuid
import requests
import html as _html
from urllib.parse import urlparse, parse_qs, unquote
from typing import List, Optional, Dict, Any, Type, Tuple
from datetime import datetime, timedelta
import scripts.db as db
from scripts.scuttle import Connector, ArtifactDraft, IngestResult, ScuttleConfig

class MissingAPIKeyError(Exception):
    pass

class ProviderNotConfiguredError(Exception):
    """Raised when a search provider is selected but lacks required non-secret config (e.g. base URL)."""
    pass

class ScuttleConfigResolver:
    """Helper to resolve scuttle configuration from environment and CLI."""
    @staticmethod
    def resolve(allow_private: bool = False) -> ScuttleConfig:
        return ScuttleConfig(
            allow_private_networks=allow_private
        )

def scrub_data(data: Any) -> Any:
    """
    Recursively scrub sensitive information from strings, dictionaries, and lists.
    - Redacts token-like strings.
    - Redacts local file paths.
    - Redacts credentials from URLs.
    """
    if isinstance(data, str):
        # 1. Redact credentials from URLs
        data = re.sub(r'(https?://)([^/:]+):([^/@]+)@', r'\1REDACTED:REDACTED@', data)
        # 2. Redact common token/key query params
        data = re.sub(r'([?&](?:api_key|token|auth|key|secret)=)[^&]+', r'\1REDACTED', data, flags=re.I)
        # 3. Redact local absolute file paths (Unix style, common patterns)
        # We redact /Users/, /home/, /root/, /etc/, /var/log/, and anything that looks like a hidden config/ssh path
        data = re.sub(r'/(?:Users|home|root|etc|var/log)/[a-zA-Z0-9._/-]+', '[REDACTED_PATH]', data)
        data = re.sub(r'~/[a-zA-Z0-9._/-]*\.(?:ssh|bash|zsh|aws|config|env|key|pem|pgp|gpg|token)[a-zA-Z0-9._/-]*', '[REDACTED_SENSITIVE_PATH]', data)
        return data
    elif isinstance(data, dict):
        sensitive_keys = {"token", "key", "secret", "password", "auth", "api_key", "apikey"}
        scrubbed = {}
        for k, v in data.items():
            if any(s in k.lower() for s in sensitive_keys) and isinstance(v, str):
                scrubbed[k] = "[REDACTED]"
            else:
                scrubbed[k] = scrub_data(v)
        return scrubbed
    elif isinstance(data, list):
        return [scrub_data(i) for i in data]
    return data

class IngestService:
    """Service to manage connector registration and ingestion routing."""
    
    def __init__(self):
        self._connectors: List[Connector] = []

    def register_connector(self, connector: Connector):
        self._connectors.append(connector)

    def get_connector_for(self, source: str) -> Optional[Connector]:
        for connector in self._connectors:
            if connector.can_handle(source):
                return connector
        return None

    def ingest(
        self,
        project_id: str,
        source: str,
        extra_tags: List[str] = None,
        branch: Optional[str] = None,
        config: Optional[ScuttleConfig] = None,
    ) -> IngestResult:
        if not config:
            config = ScuttleConfig()

        # Dedup by source URL per project+branch to avoid repeated ingestion
        branch_id = resolve_branch_id(project_id, branch)
        conn = None
        try:
            src_scrubbed = scrub_data(source)
            if src_scrubbed:
                evidence = json.dumps({"source_url": src_scrubbed})
                conn = db.get_connection()
                c = conn.cursor()
                c.execute(
                    "SELECT id FROM findings WHERE project_id=? AND branch_id=? AND evidence=? LIMIT 1",
                    (project_id, branch_id, evidence),
                )
                row = c.fetchone()
                if row and row[0]:
                    return IngestResult(
                        success=True,
                        artifact_id=row[0],
                        metadata={"dedup": True, "source": "dedup"},
                    )
        except Exception:
            pass
        finally:
            try:
                if conn is not None: conn.close()
            except Exception: pass
            
        connector = self.get_connector_for(source)
        if not connector:
            return IngestResult(success=False, error=f"No connector found for source: {source}")

        try:
            draft = connector.fetch(source, config)
            all_tags = draft.tags
            if extra_tags:
                all_tags.extend([t for t in extra_tags if t not in all_tags])
            
            finding_id = add_insight(
                project_id, 
                draft.title, 
                draft.content, 
                source_url=source, 
                tags=",".join(all_tags),
                confidence=draft.confidence,
                branch=branch,
            )
            log_event(
                project_id, 
                "INGEST", 
                "connector_fetch", 
                draft.raw_payload or {"title": draft.title},
                confidence=draft.confidence,
                source=draft.source,
                tags=",".join(all_tags),
                branch=branch,
            )
            return IngestResult(success=True, artifact_id=finding_id, metadata={"title": draft.title, "source": draft.source})
        except Exception as e:
            return IngestResult(success=False, error=str(e))

def _safe_id_part(raw: str) -> str:
    return re.sub(r\"[^a-zA-Z0-9_-]\", \"_\", (raw or \"\").strip())

def _make_branch_id(project_id: str, branch_name: str) -> str:
    return f\"br_{_safe_id_part(project_id)}_{_safe_id_part(branch_name)}\"

def ensure_branch(project_id: str, branch_name: str, parent_branch: Optional[str] = None, hypothesis: str = \"\") -> str:
    conn = db.get_connection()
    c = conn.cursor()
    now = datetime.now().isoformat()
    branch_name = (branch_name or \"main\").strip() or \"main\"
    parent_id = None
    if parent_branch:
        c.execute(\"SELECT id FROM branches WHERE project_id=? AND name=?\", (project_id, parent_branch))
        row = c.fetchone()
        if not row:
            conn.close()
            raise ValueError(f\"Parent branch '{parent_branch}' not found.\")
        parent_id = row[0]
    branch_id = _make_branch_id(project_id, branch_name)
    c.execute(
        \"INSERT OR IGNORE INTO branches (id, project_id, name, parent_id, hypothesis, status, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)\",
        (branch_id, project_id, branch_name, parent_id, hypothesis or \"\", \"active\", now),
    )
    conn.commit()
    conn.close()
    return branch_id

def resolve_branch_id(project_id: str, branch: Optional[str]) -> str:
    branch_name = (branch or \"main\").strip() or \"main\"
    conn = db.get_connection()
    c = conn.cursor()
    c.execute(\"SELECT id FROM branches WHERE project_id=? AND name=?\", (project_id, branch_name))
    row = c.fetchone()
    conn.close()
    if row: return row[0]
    if branch_name == \"main\": return ensure_branch(project_id, \"main\")
    raise ValueError(f\"Branch '{branch_name}' not found.\")

def create_branch(project_id: str, name: str, parent: Optional[str] = None, hypothesis: str = \"\") -> str:
    return ensure_branch(project_id, name, parent_branch=parent, hypothesis=hypothesis)

def list_branches(project_id: str):
    conn = db.get_connection()
    c = conn.cursor()
    c.execute(\"SELECT id, name, parent_id, hypothesis, status, created_at FROM branches WHERE project_id=? ORDER BY created_at ASC\", (project_id,))
    rows = c.fetchall()
    conn.close()
    return rows

def add_hypothesis(project_id: str, branch: str, statement: str, rationale: str = \"\", confidence: float = 0.5, status: str = \"open\"):
    branch_id = resolve_branch_id(project_id, branch)
    conn = db.get_connection()
    c = conn.cursor()
    now = datetime.now().isoformat()
    hypothesis_id = f\"hyp_{uuid.uuid4().hex[:10]}\"
    c.execute(\"INSERT INTO hypotheses (id, branch_id, statement, rationale, confidence, status, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?)\", (hypothesis_id, branch_id, statement, rationale or \"\", confidence, status, now, now))
    conn.commit()
    conn.close()
    return hypothesis_id

def list_hypotheses(project_id: str, branch: Optional[str] = None):
    conn = db.get_connection()
    c = conn.cursor()
    if branch:
        branch_id = resolve_branch_id(project_id, branch)
        c.execute(\"SELECT h.id, b.name, h.statement, h.rationale, h.confidence, h.status, h.created_at, h.updated_at FROM hypotheses h JOIN branches b ON b.id = h.branch_id WHERE b.project_id=? AND h.branch_id=? ORDER BY h.created_at DESC\", (project_id, branch_id))
    else:
        c.execute(\"SELECT h.id, b.name, h.statement, h.rationale, h.confidence, h.status, h.created_at, h.updated_at FROM hypotheses h JOIN branches b ON b.id = h.branch_id WHERE b.project_id=? ORDER BY h.created_at DESC\", (project_id,))
    rows = c.fetchall()
    conn.close()
    return rows

def perform_brave_search(query):
    api_key = os.environ.get(\"BRAVE_API_KEY\")
    if not api_key: raise MissingAPIKeyError(\"BRAVE_API_KEY not found.\")
    url = \"https://api.search.brave.com/res/v1/web/search\"
    headers = {\"X-Subscription-Token\": api_key, \"Accept\": \"application/json\"}
    params = {\"q\": query}
    s = requests.Session()
    s.trust_env = False
    response = s.get(url, headers=headers, params=params, timeout=20)
    response.raise_for_status()
    data = response.json()
    if isinstance(data, dict) and \"provider\" not in data: data[\"provider\"] = \"brave\"
    return data

def perform_serper_search(query: str) -> dict:
    api_key = os.environ.get(\"SERPER_API_KEY\")
    if not api_key: raise MissingAPIKeyError(\"SERPER_API_KEY not found.\")
    url = \"https://google.serper.dev/search\"
    headers = {\"X-API-KEY\": api_key, \"Content-Type\": \"application/json\", \"Accept\": \"application/json\"}
    payload = {\"q\": query}
    s = requests.Session()
    s.trust_env = False
    resp = s.post(url, headers=headers, json=payload, timeout=25)
    resp.raise_for_status()
    raw = resp.json()
    results = []
    organic = raw.get(\"organic\", []) if isinstance(raw, dict) else []
    for r in organic:
        if not isinstance(r, dict): continue
        link, title, snippet = (r.get(\"link\") or \"\").strip(), (r.get(\"title\") or \"\").strip(), (r.get(\"snippet\") or \"\").strip()
        if link and title: results.append({\"url\": link, \"title\": title, \"description\": snippet})
    return {\"provider\": \"serper\", \"web\": {\"results\": results}, \"raw\": raw}

def perform_searxng_search(query: str) -> dict:
    base = (os.environ.get(\"SEARXNG_BASE_URL\") or \"\").strip()
    if not base: raise ProviderNotConfiguredError(\"SEARXNG_BASE_URL not configured.\")
    url = base.rstrip(\"/\") + \"/search\"
    params = {\"q\": query, \"format\": \"json\"}
    s = requests.Session()
    s.trust_env = False
    resp = s.get(url, params=params, timeout=25)
    resp.raise_for_status()
    raw = resp.json()
    results = []
    rows = raw.get(\"results\", []) if isinstance(raw, dict) else []
    for r in rows:
        if not isinstance(r, dict): continue
        link, title, content = (r.get(\"url\") or \"\").strip(), (r.get(\"title\") or \"\").strip(), (r.get(\"content\") or r.get(\"description\") or \"\").strip()
        if link and title:
            content = re.sub(r\"<[^>]+>\", \"\", content)
            results.append({\"url\": link, \"title\": title, \"description\": content})
    return {\"provider\": \"searxng\", \"web\": {\"results\": results}, \"raw\": raw}

def _ddg_decode_url(href: str) -> str:
    h = (href or \"\").strip()
    if not h: return \"\"
    if h.startswith(\"//\"): h = \"https:\" + h
    if h.startswith(\"/\"): h = \"https://duckduckgo.com\" + h
    try:
        p = urlparse(h)
        uddg = parse_qs(p.query or \"\").get(\"uddg\")
        if uddg and isinstance(uddg, list) and isinstance(uddg[0], str): return unquote(uddg[0])
    except Exception: pass
    return h

def perform_duckduckgo_search(query: str, *, max_results: int = 8) -> dict:
    try: from bs4 import BeautifulSoup
    except Exception as e: raise RuntimeError(f\"bs4 not available: {e}\")
    s = requests.Session()
    s.trust_env = False
    headers = {\"User-Agent\": \"ResearchVault/1.2 (+https://github.com/lraivisto/ResearchVault)\", \"Accept-Language\": \"en-US,en;q=0.9\"}
    url = \"https://html.duckduckgo.com/html/\"
    resp = s.get(url, params={\"q\": query}, headers=headers, timeout=25)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text or \"\", \"html.parser\")
    results = []
    for a in soup.select(\"a.result__a\"):
        title, href = a.get_text(\" \", strip=True), _ddg_decode_url(a.get(\"href\") or \"\")
        if not title or not href: continue
        snippet = \"\"
        parent = a.find_parent(\"div\", class_=re.compile(r\"result\")) or a.parent
        if parent:
            sn = parent.select_one(\".result__snippet\") or parent.select_one(\".result__snippet--body\")
            if sn: snippet = sn.get_text(\" \", strip=True)
        results.append({\"url\": href, \"title\": title, \"description\": snippet})
        if len(results) >= max_results: break
    return {\"provider\": \"duckduckgo\", \"web\": {\"results\": results}}

def perform_wikipedia_search(query: str, *, max_results: int = 8, lang: str = \"en\") -> dict:
    base = f\"https://{(lang or 'en').strip().lower()}.wikipedia.org\"
    url = base + \"/w/api.php\"
    params = {\"action\": \"query\", \"list\": \"search\", \"srsearch\": query, \"format\": \"json\", \"utf8\": 1, \"srlimit\": int(max_results)}
    s = requests.Session()
    s.trust_env = False
    resp = s.get(url, params=params, timeout=20)
    resp.raise_for_status()
    raw = resp.json()
    rows = raw.get(\"query\", {}).get(\"search\", []) if isinstance(raw, dict) else []
    results = []
    for r in rows:
        if not isinstance(r, dict): continue
        title, snippet = (r.get(\"title\") or \"\").strip(), re.sub(r\"<[^>]+>\", \"\", (r.get(\"snippet\") or \"\").strip())
        snippet = _html.unescape(snippet)
        if not title: continue
        results.append({\"url\": base + \"/wiki/\" + requests.utils.quote(title.replace(\" \", \"_\")), \"title\": title, \"description\": snippet})
    return {\"provider\": \"wikipedia\", \"web\": {\"results\": results}, \"raw\": raw}

def _search_cache_key(query: str, provider: str) -> str:
    return hashlib.sha256(f\"{(provider or 'brave').strip().lower()}:{_normalize_query(query)}\".encode()).hexdigest()

def log_search(query, result, provider: str = \"brave\"):
    conn = db.get_connection()
    c = conn.cursor()
    c.execute(\"INSERT OR REPLACE INTO search_cache VALUES (?, ?, ?, ?)\", (_search_cache_key(query, provider), query, json.dumps(result), datetime.now().isoformat()))
    conn.commit()
    conn.close()

def check_search(query, ttl_hours=24, provider: str = \"brave\"):
    conn = db.get_connection()
    c = conn.cursor()
    c.execute(\"SELECT result, timestamp FROM search_cache WHERE query_hash=?\", (_search_cache_key(query, provider),))
    row = c.fetchone()
    conn.close()
    if row:
        result, timestamp = row
        try:
            if datetime.now() - datetime.fromisoformat(timestamp) < timedelta(hours=ttl_hours): return json.loads(result)
        except ValueError: pass
    return None

def search(query: str, *, provider: str = \"auto\", providers: Optional[list[str]] = None, ttl_hours: int = 24) -> tuple[dict, str, str]:
    q = (query or \"\").strip()
    if not q: raise ValueError(\"empty query\")
    p = (provider or \"auto\").strip().lower()
    order = providers or (default_search_providers() if p == \"auto\" else [p])
    for prov in order:
        cached = check_search(q, ttl_hours=ttl_hours, provider=prov)
        if cached is not None: return cached, \"cache\", prov
    last_missing, last_other = None, None
    for prov in order:
        fn = {\"brave\": perform_brave_search, \"serper\": perform_serper_search, \"searxng\": perform_searxng_search, \"duckduckgo\": perform_duckduckgo_search, \"wikipedia\": perform_wikipedia_search}.get(prov)
        if not fn: continue
        try:
            res = fn(q)
            log_search(q, res, provider=prov)
            return res, \"network\", prov
        except MissingAPIKeyError as e: last_missing = e
        except ProviderNotConfiguredError as e: last_other = e
        except Exception as e: last_other = e
    if last_missing and p != \"auto\": raise last_missing
    raise RuntimeError(str(last_other or last_missing or \"search failed\"))

def default_search_providers():
    env = os.getenv(\"RESEARCHVAULT_SEARCH_PROVIDERS\")
    return [p.strip().lower() for p in env.split(\",\") if p.strip()] if env else [\"brave\", \"serper\", \"searxng\", \"duckduckgo\", \"wikipedia\"]

@db.retry_on_lock()
def start_project(project_id, name, objective, priority=0, silent: bool = False):
    conn = db.get_connection()
    c = conn.cursor()
    c.execute(\"INSERT OR IGNORE INTO projects (id, name, objective, status, created_at, priority) VALUES (?, ?, ?, ?, ?, ?)\", (project_id, name, objective, \"active\", datetime.now().isoformat(), priority))
    conn.commit()
    conn.close()
    ensure_branch(project_id, \"main\")
    if not silent: print(f\"Project '{name}' initialized.\")

@db.retry_on_lock()
def log_event(project_id, event_type, step, payload, confidence=1.0, source=\"unknown\", tags=\"\", branch: Optional[str] = None):
    conn, now = db.get_connection(), datetime.now().isoformat()
    c = conn.cursor()
    c.execute(\"INSERT INTO events (project_id, event_type, step, payload, confidence, source, tags, timestamp, branch_id) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)\", (project_id, event_type, step, json.dumps(scrub_data(payload)), confidence, scrub_data(source), tags, now, resolve_branch_id(project_id, branch)))
    conn.commit()
    conn.close()

def get_status(project_id, tag_filter=None, branch: Optional[str] = None):
    conn = db.get_connection()
    c = conn.cursor()
    c.execute(\"SELECT * FROM projects WHERE id=?\", (project_id,))
    project = c.fetchone()
    if not project:
        conn.close()
        return None
    branch_id = resolve_branch_id(project_id, branch)
    query = \"SELECT event_type, step, payload, confidence, source, timestamp, tags FROM events WHERE project_id=? AND branch_id=?\"
    params = [project_id, branch_id]
    if tag_filter:
        query += \" AND tags LIKE ?\"
        params.append(f\"%{tag_filter}%\")
    c.execute(query + \" ORDER BY id DESC LIMIT 10\", params)
    events = c.fetchall()
    conn.close()
    return {\"project\": project, \"recent_events\": events}

def update_status(project_id, status=None, priority=None):
    conn = db.get_connection()
    c = conn.cursor()
    if status: c.execute(\"UPDATE projects SET status=? WHERE id=?\", (status, project_id))
    if priority is not None: c.execute(\"UPDATE projects SET priority=? WHERE id=?\", (priority, project_id))
    conn.commit()
    conn.close()

def list_projects():
    conn = db.get_connection()
    c = conn.cursor()
    c.execute(\"SELECT * FROM projects ORDER BY priority DESC, created_at DESC\")
    rows = c.fetchall()
    conn.close()
    return rows

@db.retry_on_lock()
def add_insight(project_id, title, content, source_url=\"\", tags=\"\", confidence=1.0, branch: Optional[str] = None):
    conn, now = db.get_connection(), datetime.now().isoformat()
    fid = f\"fnd_{uuid.uuid4().hex[:8]}\"
    c = conn.cursor()
    c.execute(\"INSERT INTO findings (id, project_id, title, content, evidence, confidence, tags, created_at, branch_id) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)\", (fid, project_id, scrub_data(title), scrub_data(content), json.dumps({\"source_url\": scrub_data(source_url)}), confidence, tags, now, resolve_branch_id(project_id, branch)))
    conn.commit()
    conn.close()
    return fid

@db.retry_on_lock()
def add_artifact(project_id: str, path: str, type: str = \"FILE\", metadata: Optional[Dict[str, Any]] = None, branch: Optional[str] = None) -> str:
    abs_path = os.path.abspath(os.path.expanduser(path))
    workspace_root, vault_root = os.path.abspath(os.path.expanduser(\"~/.openclaw/workspace\")), os.path.abspath(os.path.expanduser(\"~/.researchvault\"))
    if not any(abs_path.startswith(r) for r in [workspace_root, vault_root]) and not any(x in abs_path for x in [\"PYTEST\", \"tmp\", \"TEMP\"]):
        raise ValueError(\"Security violation: path outside allowed boundaries\")
    aid, now = f\"art_{uuid.uuid4().hex[:10]}\", datetime.now().isoformat()
    conn = db.get_connection()
    c = conn.cursor()
    c.execute(\"INSERT INTO artifacts (id, project_id, type, path, metadata, created_at, branch_id) VALUES (?, ?, ?, ?, ?, ?, ?)\", (aid, project_id, type, scrub_data(path), json.dumps(scrub_data(metadata or {})), now, resolve_branch_id(project_id, branch)))
    conn.commit()
    conn.close()
    log_event(project_id, \"ARTIFACT\", \"add\", {\"artifact_id\": aid, \"path\": path}, source=\"vault\", tags=\"artifact\", branch=branch)
    return aid

def list_artifacts(project_id: str, branch: Optional[str] = None):
    conn = db.get_connection()
    c = conn.cursor()
    c.execute(\"SELECT id, type, path, metadata, created_at FROM artifacts WHERE project_id=? AND branch_id=? ORDER BY created_at DESC\", (project_id, resolve_branch_id(project_id, branch)))
    rows = c.fetchall()
    conn.close()
    return rows

def plan_verification_missions(project_id: str, branch: Optional[str] = None, *, threshold: float = 0.7, max_missions: int = 20):
    branch_id = resolve_branch_id(project_id, branch)
    conn, now = db.get_connection(), datetime.now().isoformat()
    c = conn.cursor()
    c.execute(\"SELECT id, title, content, evidence, tags, confidence FROM findings WHERE project_id=? AND branch_id=? AND (confidence < ? OR tags LIKE '%unverified%') ORDER BY confidence ASC, created_at DESC\", (project_id, branch_id, float(threshold)))
    findings, inserted = c.fetchall(), []
    for fid, title, content, evidence, tags, confidence in findings:
        if len(inserted) >= max_missions: break
        keywords = _extract_keywords(f\"{title}\\n{content}\", limit=6)
        q = title or \" \".join(keywords)
        qhash, mid = _query_hash(q), f\"mis_{uuid.uuid4().hex[:10]}\"
        c.execute(\"INSERT OR IGNORE INTO verification_missions (id, project_id, branch_id, finding_id, mission_type, query, query_hash, question, rationale, status, priority, result_meta, last_error, created_at, updated_at, dedup_hash) VALUES (?, ?, ?, ?, 'SEARCH', ?, ?, ?, ?, 'open', ?, '', '', ?, ?, ?)\", (mid, project_id, branch_id, fid, q, qhash, f\"Corroborate: {title}\", \"Auto-gen\", int((1-float(confidence))*100), now, now, hashlib.sha256(f\"{project_id}|{branch_id}|{fid}|{qhash}\".encode()).hexdigest()))
        if c.rowcount == 1: inserted.append((mid, fid, q))
    conn.commit()
    conn.close()
    if inserted: log_event(project_id, \"VERIFY\", \"plan\", {\"missions\": len(inserted)}, confidence=0.9, source=\"vault\", tags=\"verify\", branch=branch)
    return inserted

def list_verification_missions(project_id: str, branch: Optional[str] = None, *, status: Optional[str] = None, limit: int = 50):
    conn = db.get_connection()
    c = conn.cursor()
    q = \"SELECT m.id, m.status, m.priority, m.query, f.title, f.confidence, m.created_at, m.completed_at, m.last_error FROM verification_missions m JOIN findings f ON f.id = m.finding_id WHERE m.project_id=? AND m.branch_id=?\"
    params = [project_id, resolve_branch_id(project_id, branch)]
    if status: q += \" AND m.status=?\"; params.append(status)
    c.execute(q + \" ORDER BY m.priority DESC, m.created_at ASC LIMIT ?\", params + [int(limit)])
    rows = c.fetchall()
    conn.close()
    return rows

def run_verification_missions(project_id: str, branch: Optional[str] = None, *, status: str = \"open\", limit: int = 5):
    branch_id = resolve_branch_id(project_id, branch)
    conn, now = db.get_connection(), datetime.now().isoformat()
    c = conn.cursor()
    c.execute(\"SELECT id, query FROM verification_missions WHERE project_id=? AND branch_id=? AND status=? ORDER BY priority DESC, created_at ASC LIMIT ?\", (project_id, branch_id, status, int(limit)))
    rows, results = c.fetchall(), []
    for mid, q in rows:
        c.execute(\"UPDATE verification_missions SET status='in_progress', updated_at=? WHERE id=?\", (now, mid)); conn.commit()
        try:
            res, src, prov = search(q, provider=\"auto\")
            meta = {\"query_hash\": _query_hash(q), \"provider\": prov, \"source\": src}
            c.execute(\"UPDATE verification_missions SET status='done', result_meta=?, updated_at=?, completed_at=? WHERE id=?\", (json.dumps(meta), now, now, mid)); conn.commit()
            log_event(project_id, \"VERIFY\", \"run\", {\"mission_id\": mid, \"query\": q}, confidence=0.85, source=\"vault\", tags=\"verify\", branch=branch)
            results.append({\"id\": mid, \"status\": \"done\", \"query\": q, \"meta\": meta})
        except Exception as e:
            c.execute(\"UPDATE verification_missions SET status='open', last_error=?, updated_at=? WHERE id=?\", (str(e), now, mid)); conn.commit()
            results.append({\"id\": mid, \"status\": \"open\", \"error\": str(e)})
    conn.close()
    return results

def get_ingest_service():
    from scripts.scuttle import RedditScuttler, MoltbookScuttler, GrokipediaConnector, YouTubeConnector, WebScuttler
    s = IngestService()
    for c in [RedditScuttler(), MoltbookScuttler(), GrokipediaConnector(), YouTubeConnector(), WebScuttler()]: s.register_connector(c)
    return s
