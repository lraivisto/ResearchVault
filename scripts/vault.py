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
                 (id TEXT PRIMARY KEY, name TEXT, objective TEXT, status TEXT, created_at TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS events
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, project_id TEXT, event_type TEXT, 
                  step INTEGER, payload TEXT, timestamp TEXT,
                  FOREIGN KEY(project_id) REFERENCES projects(id))''')
    conn.commit()
    conn.close()

def start_project(project_id, name, objective):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    now = datetime.now().isoformat()
    c.execute("INSERT OR IGNORE INTO projects VALUES (?, ?, ?, ?, ?)", 
              (project_id, name, objective, 'active', now))
    conn.commit()
    conn.close()
    print(f"Project '{name}' ({project_id}) initialized.")

def log_event(project_id, event_type, step, payload):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    now = datetime.now().isoformat()
    c.execute("INSERT INTO events (project_id, event_type, step, payload, timestamp) VALUES (?, ?, ?, ?, ?)",
              (project_id, event_type, step, json.dumps(payload), now))
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
    c.execute("SELECT event_type, step, payload, timestamp FROM events WHERE project_id=? ORDER BY id DESC LIMIT 10", (project_id,))
    events = c.fetchall()
    conn.close()
    return {"project": project, "recent_events": events}

def update_status(project_id, status):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("UPDATE projects SET status=? WHERE id=?", (status, project_id))
    conn.commit()
    conn.close()
    print(f"Project '{project_id}' status updated to '{status}'.")

def list_projects():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT * FROM projects ORDER BY created_at DESC")
    projects = c.fetchall()
    conn.close()
    return projects

if __name__ == "__main__":
    init_db()
    parser = argparse.ArgumentParser(description="Vault Orchestrator")
    subparsers = parser.add_subparsers(dest="command")

    # Init
    init_parser = subparsers.add_parser("init")
    init_parser.add_argument("--id", required=True)
    init_parser.add_argument("--name")
    init_parser.add_argument("--objective", required=True)

    # List
    list_parser = subparsers.add_parser("list")

    # Status Update
    update_parser = subparsers.add_parser("update")
    update_parser.add_argument("--id", required=True)
    update_parser.add_argument("--status", choices=['active', 'paused', 'completed', 'failed'], required=True)

    # Log
    log_parser = subparsers.add_parser("log")
    log_parser.add_argument("--id", required=True)
    log_parser.add_argument("--type", required=True)
    log_parser.add_argument("--step", type=int, default=0)
    log_parser.add_argument("--payload", default="{}")

    # Status
    status_parser = subparsers.add_parser("status")
    status_parser.add_argument("--id", required=True)

    args = parser.parse_args()

    if args.command == "init":
        start_project(args.id, args.name or args.id, args.objective)
    elif args.command == "list":
        projects = list_projects()
        if not projects:
            print("No projects found.")
        for p in projects:
            print(f"[{p[3].upper()}] {p[0]}: {p[1]} - {p[2]} ({p[4]})")
    elif args.command == "update":
        update_status(args.id, args.status)
    elif args.command == "log":
        log_event(args.id, args.type, args.step, json.loads(args.payload))
        print(f"Logged {args.type} for {args.id}")
    elif args.command == "status":
        print(json.dumps(get_status(args.id), indent=2))
