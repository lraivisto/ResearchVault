import json
import sqlite3
import hashlib
import os
import re
import uuid
import requests
from typing import List, Optional, Dict, Any, Type
from datetime import datetime, timedelta
import scripts.db as db
from scripts.scuttle import Connector, ArtifactDraft, IngestResult

class MissingAPIKeyError(Exception):
    pass

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
    ) -> IngestResult:
        connector = self.get_connector_for(source)
        if not connector:
            return IngestResult(success=False, error=f"No connector found for source: {source}")

        try:
            draft = connector.fetch(source)
            
            # Merge tags
            all_tags = draft.tags
            if extra_tags:
                all_tags.extend([t for t in extra_tags if t not in all_tags])
            
            # Add to database (Finding table)
            add_insight(
                project_id, 
                draft.title, 
                draft.content, 
                source_url=source, 
                tags=",".join(all_tags),
                confidence=draft.confidence,
                branch=branch,
            )
            # Log event
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
            return IngestResult(success=True, metadata={"title": draft.title, "source": draft.source})
        except Exception as e:
            return IngestResult(success=False, error=str(e))

def _safe_id_part(raw: str) -> str:
    return re.sub(r"[^a-zA-Z0-9_-]", "_", (raw or "").strip())

def _make_branch_id(project_id: str, branch_name: str) -> str:
    return f"br_{_safe_id_part(project_id)}_{_safe_id_part(branch_name)}"

def ensure_branch(project_id: str, branch_name: str, parent_branch: Optional[str] = None, hypothesis: str = "") -> str:
    """Create a branch if missing and return its branch_id."""
    conn = db.get_connection()
    c = conn.cursor()
    now = datetime.now().isoformat()

    branch_name = (branch_name or "main").strip()
    if not branch_name:
        branch_name = "main"

    parent_id = None
    if parent_branch:
        c.execute("SELECT id FROM branches WHERE project_id=? AND name=?", (project_id, parent_branch))
        row = c.fetchone()
        if not row:
            conn.close()
            raise ValueError(f"Parent branch '{parent_branch}' not found for project '{project_id}'.")
        parent_id = row[0]

    branch_id = _make_branch_id(project_id, branch_name)
    c.execute(
        "INSERT OR IGNORE INTO branches (id, project_id, name, parent_id, hypothesis, status, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
        (branch_id, project_id, branch_name, parent_id, hypothesis or "", "active", now),
    )
    conn.commit()
    conn.close()
    return branch_id

def resolve_branch_id(project_id: str, branch: Optional[str]) -> str:
    """Resolve a branch name (or None) to a branch_id; defaults to the project's 'main' branch."""
    branch_name = (branch or "main").strip()
    if not branch_name:
        branch_name = "main"

    conn = db.get_connection()
    c = conn.cursor()
    c.execute("SELECT id FROM branches WHERE project_id=? AND name=?", (project_id, branch_name))
    row = c.fetchone()
    conn.close()
    if row:
        return row[0]

    if branch_name == "main":
        # Ensure default branch exists (for older DBs or manually-created projects).
        return ensure_branch(project_id, "main")

    raise ValueError(f"Branch '{branch_name}' not found for project '{project_id}'.")

def create_branch(project_id: str, name: str, parent: Optional[str] = None, hypothesis: str = "") -> str:
    """Create a new branch (explicit user action)."""
    return ensure_branch(project_id, name, parent_branch=parent, hypothesis=hypothesis)

def list_branches(project_id: str):
    conn = db.get_connection()
    c = conn.cursor()
    c.execute(
        "SELECT id, name, parent_id, hypothesis, status, created_at FROM branches WHERE project_id=? ORDER BY created_at ASC",
        (project_id,),
    )
    rows = c.fetchall()
    conn.close()
    return rows

def add_hypothesis(
    project_id: str,
    branch: str,
    statement: str,
    rationale: str = "",
    confidence: float = 0.5,
    status: str = "open",
):
    branch_id = resolve_branch_id(project_id, branch)
    conn = db.get_connection()
    c = conn.cursor()
    now = datetime.now().isoformat()
    hypothesis_id = f"hyp_{uuid.uuid4().hex[:10]}"
    c.execute(
        "INSERT INTO hypotheses (id, branch_id, statement, rationale, confidence, status, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        (hypothesis_id, branch_id, statement, rationale or "", confidence, status, now, now),
    )
    conn.commit()
    conn.close()
    return hypothesis_id

def list_hypotheses(project_id: str, branch: Optional[str] = None):
    conn = db.get_connection()
    c = conn.cursor()
    if branch:
        branch_id = resolve_branch_id(project_id, branch)
        c.execute(
            """SELECT h.id, b.name, h.statement, h.rationale, h.confidence, h.status, h.created_at, h.updated_at
               FROM hypotheses h
               JOIN branches b ON b.id = h.branch_id
               WHERE b.project_id=? AND h.branch_id=?
               ORDER BY h.created_at DESC""",
            (project_id, branch_id),
        )
    else:
        c.execute(
            """SELECT h.id, b.name, h.statement, h.rationale, h.confidence, h.status, h.created_at, h.updated_at
               FROM hypotheses h
               JOIN branches b ON b.id = h.branch_id
               WHERE b.project_id=?
               ORDER BY h.created_at DESC""",
            (project_id,),
        )
    rows = c.fetchall()
    conn.close()
    return rows

def perform_brave_search(query):
    api_key = os.environ.get("BRAVE_API_KEY")
    if not api_key:
        raise MissingAPIKeyError("BRAVE_API_KEY not found in environment variables.")
        
    url = "https://api.search.brave.com/res/v1/web/search"
    headers = {
        "X-Subscription-Token": api_key,
        "Accept": "application/json"
    }
    params = {"q": query}
    
    response = requests.get(url, headers=headers, params=params)
    response.raise_for_status()
    return response.json()

def log_search(query, result):
    query_hash = hashlib.sha256(query.lower().strip().encode()).hexdigest()
    conn = db.get_connection()
    c = conn.cursor()
    now = datetime.now().isoformat()
    c.execute("INSERT OR REPLACE INTO search_cache VALUES (?, ?, ?, ?)",
              (query_hash, query, json.dumps(result), now))
    conn.commit()
    conn.close()

def check_search(query, ttl_hours=24):
    query_hash = hashlib.sha256(query.lower().strip().encode()).hexdigest()
    conn = db.get_connection()
    c = conn.cursor()
    c.execute("SELECT result, timestamp FROM search_cache WHERE query_hash=?", (query_hash,))
    row = c.fetchone()
    conn.close()
    if row:
        result, timestamp = row
        try:
            cached_time = datetime.fromisoformat(timestamp)
            if datetime.now() - cached_time < timedelta(hours=ttl_hours):
                return json.loads(result)
        except ValueError:
            pass
    return None

def start_project(project_id, name, objective, priority=0):
    conn = db.get_connection()
    c = conn.cursor()
    now = datetime.now().isoformat()
    c.execute(
        "INSERT OR IGNORE INTO projects (id, name, objective, status, created_at, priority) VALUES (?, ?, ?, ?, ?, ?)",
        (project_id, name, objective, "active", now, priority),
    )
    conn.commit()
    conn.close()
    # Ensure default branch exists.
    ensure_branch(project_id, "main")
    print(f"Project '{name}' ({project_id}) initialized with priority {priority}.")

def log_event(
    project_id,
    event_type,
    step,
    payload,
    confidence=1.0,
    source="unknown",
    tags="",
    branch: Optional[str] = None,
):
    conn = db.get_connection()
    c = conn.cursor()
    now = datetime.now().isoformat()
    branch_id = resolve_branch_id(project_id, branch)
    c.execute(
        "INSERT INTO events (project_id, event_type, step, payload, confidence, source, tags, timestamp, branch_id) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (project_id, event_type, step, json.dumps(payload), confidence, source, tags, now, branch_id),
    )
    conn.commit()
    conn.close()

def get_status(project_id, tag_filter=None, branch: Optional[str] = None):
    conn = db.get_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM projects WHERE id=?", (project_id,))
    project = c.fetchone()
    if not project:
        conn.close()
        return None
    
    branch_id = resolve_branch_id(project_id, branch)
    query = "SELECT event_type, step, payload, confidence, source, timestamp, tags FROM events WHERE project_id=? AND branch_id=?"
    params = [project_id, branch_id]
    if tag_filter:
        query += " AND tags LIKE ?"
        params.append(f"%{tag_filter}%")
    query += " ORDER BY id DESC LIMIT 10"
    
    c.execute(query, params)
    events = c.fetchall()
    conn.close()
    return {"project": project, "recent_events": events}

def update_status(project_id, status=None, priority=None):
    try:
        conn = db.get_connection()
        c = conn.cursor()
        if status:
            c.execute("UPDATE projects SET status=? WHERE id=?", (status, project_id))
            if c.rowcount == 0:
                print(f"Error: Project '{project_id}' not found.")
            else:
                print(f"Project '{project_id}' status updated to '{status}'.")
        if priority is not None:
            c.execute("UPDATE projects SET priority=? WHERE id=?", (priority, project_id))
            if c.rowcount == 0:
                print(f"Error: Project '{project_id}' not found.")
            else:
                print(f"Project '{project_id}' priority updated to {priority}.")
        conn.commit()
    except sqlite3.Error as e:
        print(f"Database error: {e}")
    finally:
        if conn:
            conn.close()

def list_projects():
    conn = db.get_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM projects ORDER BY priority DESC, created_at DESC")
    projects = c.fetchall()
    conn.close()
    return projects

def add_insight(project_id, title, content, source_url="", tags="", confidence=1.0, branch: Optional[str] = None):
    conn = db.get_connection()
    c = conn.cursor()
    now = datetime.now().isoformat()
    finding_id = f"fnd_{uuid.uuid4().hex[:8]}"
    evidence = json.dumps({"source_url": source_url})
    branch_id = resolve_branch_id(project_id, branch)
    c.execute(
        """INSERT INTO findings (id, project_id, title, content, evidence, confidence, tags, created_at, branch_id)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (finding_id, project_id, title, content, evidence, confidence, tags, now, branch_id),
    )
    conn.commit()
    conn.close()

def get_insights(project_id, tag_filter=None, branch: Optional[str] = None):
    conn = db.get_connection()
    c = conn.cursor()
    # Migration v2 uses 'findings' table.
    branch_id = resolve_branch_id(project_id, branch)
    if tag_filter:
        c.execute(
            "SELECT title, content, evidence, tags, created_at, confidence FROM findings WHERE project_id=? AND branch_id=? AND tags LIKE ? ORDER BY created_at DESC",
            (project_id, branch_id, f"%{tag_filter}%"),
        )
    else:
        c.execute(
            "SELECT title, content, evidence, tags, created_at, confidence FROM findings WHERE project_id=? AND branch_id=? ORDER BY created_at DESC",
            (project_id, branch_id),
        )
    rows = c.fetchall()
    conn.close()
    return rows

def get_ingest_service():
    """Returns a pre-configured IngestService with all connectors registered."""
    from scripts.scuttle import RedditScuttler, MoltbookScuttler, GrokipediaConnector, YouTubeConnector, WebScuttler
    service = IngestService()
    service.register_connector(RedditScuttler())
    service.register_connector(MoltbookScuttler())
    service.register_connector(GrokipediaConnector())
    service.register_connector(YouTubeConnector())
    service.register_connector(WebScuttler())
    return service
