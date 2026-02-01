import sqlite3
import json
import os
import argparse
from datetime import datetime

# Path to the research database
DB_PATH = os.path.expanduser("~/.openclaw/workspace/memory/research_vault.db")

def init_db():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS projects
                 (id TEXT PRIMARY KEY, name TEXT, objective TEXT, status TEXT, created_at TEXT, priority INTEGER DEFAULT 0)''')
    c.execute('''CREATE TABLE IF NOT EXISTS events
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, project_id TEXT, event_type TEXT, 
                  step INTEGER, payload TEXT, confidence REAL, timestamp TEXT,
                  FOREIGN KEY(project_id) REFERENCES projects(id))''')
    
    # Migration: Add priority and confidence columns if they don't exist
    c.execute("PRAGMA table_info(projects)")
    if 'priority' not in [col[1] for col in c.fetchall()]:
        c.execute("ALTER TABLE projects ADD COLUMN priority INTEGER DEFAULT 0")

    c.execute("PRAGMA table_info(events)")
    columns = [col[1] for col in c.fetchall()]
    if 'confidence' not in columns:
        c.execute("ALTER TABLE events ADD COLUMN confidence REAL DEFAULT 1.0")
        
    c.execute('''CREATE TABLE IF NOT EXISTS search_cache
                 (query_hash TEXT PRIMARY KEY, query TEXT, result TEXT, timestamp TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS insights
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, project_id TEXT, title TEXT, 
                  content TEXT, source_url TEXT, tags TEXT, timestamp TEXT,
                  FOREIGN KEY(project_id) REFERENCES projects(id))''')
    conn.commit()
    conn.close()

def log_search(query, result):
    import hashlib
    query_hash = hashlib.sha256(query.lower().strip().encode()).hexdigest()
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    now = datetime.now().isoformat()
    c.execute("INSERT OR REPLACE INTO search_cache VALUES (?, ?, ?, ?)",
              (query_hash, query, json.dumps(result), now))
    conn.commit()
    conn.close()

def check_search(query, ttl_hours=24):
    import hashlib
    from datetime import datetime, timedelta
    query_hash = hashlib.sha256(query.lower().strip().encode()).hexdigest()
    conn = sqlite3.connect(DB_PATH)
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
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    now = datetime.now().isoformat()
    c.execute("INSERT OR IGNORE INTO projects VALUES (?, ?, ?, ?, ?, ?)", 
              (project_id, name, objective, 'active', now, priority))
    conn.commit()
    conn.close()
    print(f"Project '{name}' ({project_id}) initialized with priority {priority}.")

def log_event(project_id, event_type, step, payload, confidence=1.0):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    now = datetime.now().isoformat()
    c.execute("INSERT INTO events (project_id, event_type, step, payload, confidence, timestamp) VALUES (?, ?, ?, ?, ?, ?)",
              (project_id, event_type, step, json.dumps(payload), confidence, now))
    conn.commit()
    conn.close()

def get_status(project_id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT * FROM projects WHERE id=?", (project_id,))
    project = c.fetchone()
    if not project:
        conn.close()
        return None
    c.execute("SELECT event_type, step, payload, confidence, timestamp FROM events WHERE project_id=? ORDER BY id DESC LIMIT 10", (project_id,))
    events = c.fetchall()
    conn.close()
    return {"project": project, "recent_events": events}

def update_status(project_id, status=None, priority=None):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    if status:
        c.execute("UPDATE projects SET status=? WHERE id=?", (status, project_id))
        print(f"Project '{project_id}' status updated to '{status}'.")
    if priority is not None:
        c.execute("UPDATE projects SET priority=? WHERE id=?", (priority, project_id))
        print(f"Project '{project_id}' priority updated to {priority}.")
    conn.commit()
    conn.close()

def list_projects():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT * FROM projects ORDER BY priority DESC, created_at DESC")
    projects = c.fetchall()
    conn.close()
    return projects

def add_insight(project_id, title, content, source_url="", tags=""):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    now = datetime.now().isoformat()
    c.execute("INSERT INTO insights (project_id, title, content, source_url, tags, timestamp) VALUES (?, ?, ?, ?, ?, ?)",
              (project_id, title, content, source_url, tags, now))
    conn.commit()
    conn.close()

def get_insights(project_id, tag_filter=None):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    if tag_filter:
        c.execute("SELECT title, content, source_url, tags, timestamp FROM insights WHERE project_id=? AND tags LIKE ? ORDER BY id DESC", 
                  (project_id, f"%{tag_filter}%"))
    else:
        c.execute("SELECT title, content, source_url, tags, timestamp FROM insights WHERE project_id=? ORDER BY id DESC", (project_id,))
    rows = c.fetchall()
    conn.close()
    return rows

if __name__ == "__main__":
    init_db()
    parser = argparse.ArgumentParser(description="Vault Orchestrator")
    subparsers = parser.add_subparsers(dest="command")

    # Init
    init_parser = subparsers.add_parser("init")
    init_parser.add_argument("--id", required=True)
    init_parser.add_argument("--name")
    init_parser.add_argument("--objective", required=True)
    init_parser.add_argument("--priority", type=int, default=0)

    # List
    list_parser = subparsers.add_parser("list")

    # Status Update
    update_parser = subparsers.add_parser("update")
    update_parser.add_argument("--id", required=True)
    update_parser.add_argument("--status", choices=['active', 'paused', 'completed', 'failed'], required=True)
    update_parser.add_argument("--priority", type=int, help="Update project priority")

    # Search Cache
    cache_parser = subparsers.add_parser("cache")
    cache_parser.add_argument("--query", required=True)
    cache_parser.add_argument("--set-result")

    # Log
    log_parser = subparsers.add_parser("log")
    log_parser.add_argument("--id", required=True)
    log_parser.add_argument("--type", required=True)
    log_parser.add_argument("--step", type=int, default=0)
    log_parser.add_argument("--payload", default="{}")
    log_parser.add_argument("--conf", type=float, default=1.0, help="Confidence score (0.0-1.0)")

    # Status
    status_parser = subparsers.add_parser("status")
    status_parser.add_argument("--id", required=True)

    # Insights
    insight_parser = subparsers.add_parser("insight")
    insight_parser.add_argument("--id", required=True)
    insight_parser.add_argument("--add", action="store_true")
    insight_parser.add_argument("--title")
    insight_parser.add_argument("--content")
    insight_parser.add_argument("--url", default="")
    insight_parser.add_argument("--tags", default="")
    insight_parser.add_argument("--filter-tag", help="Filter insights by tag")

    args = parser.parse_args()

    if args.command == "init":
        start_project(args.id, args.name or args.id, args.objective, args.priority)
    elif args.command == "list":
        projects = list_projects()
        if not projects:
            print("No projects found.")
        for p in projects:
            print(f"[{p[3].upper()}] (P{p[5]}) {p[0]}: {p[1]} - {p[2]} ({p[4]})")
    elif args.command == "update":
        update_status(args.id, args.status, args.priority)
    elif args.command == "cache":
        if args.set_result:
            log_search(args.query, json.loads(args.set_result))
            print(f"Cached result for: {args.query}")
        else:
            result = check_search(args.query)
            if result:
                print(json.dumps(result, indent=2))
            else:
                print("No cached result found.")
    elif args.command == "log":
        log_event(args.id, args.type, args.step, json.loads(args.payload), args.conf)
        print(f"Logged {args.type} for {args.id} (conf: {args.conf})")
    elif args.command == "status":
        status = get_status(args.id)
        if not status:
            print(f"Project '{args.id}' not found.")
        else:
            p = status['project']
            print(f"\n--- Project: {p[1]} ({p[0]}) ---")
            print(f"Status: {p[3].upper()}")
            print(f"Objective: {p[2]}")
            print(f"Created: {p[4]}")
            print("\nRecent Events:")
            for e in status['recent_events']:
                print(f"  [{e[4]}] {e[0]} (Step {e[1]}) [Conf: {e[3]}]: {e[2]}")
            
            insights = get_insights(args.id)
            if insights:
                print("\nCaptured Insights:")
                for i in insights:
                    print(f"  * {i[0]}: {i[1]} ({i[2]})")
            print("-" * 30 + "\n")
    elif args.command == "insight":
        if args.add:
            if not args.title or not args.content:
                print("Error: --title and --content required for adding insight.")
            else:
                add_insight(args.id, args.title, args.content, args.url, args.tags)
                print(f"Added insight to project '{args.id}'.")
        else:
            insights = get_insights(args.id, tag_filter=args.filter_tag)
            if not insights:
                print("No insights found" + (f" with tag '{args.filter_tag}'" if args.filter_tag else ""))
            for i in insights:
                print(f"[{i[4]}] {i[0]}\nContent: {i[1]}\nSource: {i[2]}\nTags: {i[3]}\n")
