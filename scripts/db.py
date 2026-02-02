import sqlite3
import os

# Path to the research database
DB_PATH = os.path.expanduser("~/.openclaw/workspace/memory/research_vault.db")

def get_connection():
    """Returns a connection to the SQLite database."""
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    return sqlite3.connect(DB_PATH)

def init_db():
    """Initialize the database with tables and perform migrations."""
    conn = get_connection()
    c = conn.cursor()
    
    # Core Tables
    c.execute('''CREATE TABLE IF NOT EXISTS projects
                 (id TEXT PRIMARY KEY, name TEXT, objective TEXT, status TEXT, created_at TEXT, priority INTEGER DEFAULT 0)''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS events
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, project_id TEXT, event_type TEXT, 
                  step INTEGER, payload TEXT, confidence REAL, source TEXT, tags TEXT, timestamp TEXT,
                  FOREIGN KEY(project_id) REFERENCES projects(id))''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS search_cache
                 (query_hash TEXT PRIMARY KEY, query TEXT, result TEXT, timestamp TEXT)''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS insights
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, project_id TEXT, title TEXT, 
                  content TEXT, source_url TEXT, tags TEXT, timestamp TEXT,
                  FOREIGN KEY(project_id) REFERENCES projects(id))''')

    # Migrations
    _run_migrations(c)
    
    conn.commit()
    conn.close()

def _run_migrations(cursor):
    """Run pending migrations to update schema."""
    # Migration: Add priority to projects
    cursor.execute("PRAGMA table_info(projects)")
    if 'priority' not in [col[1] for col in cursor.fetchall()]:
        cursor.execute("ALTER TABLE projects ADD COLUMN priority INTEGER DEFAULT 0")

    # Migration: Add confidence, source, tags to events
    cursor.execute("PRAGMA table_info(events)")
    columns = [col[1] for col in cursor.fetchall()]
    if 'confidence' not in columns:
        cursor.execute("ALTER TABLE events ADD COLUMN confidence REAL DEFAULT 1.0")
    if 'source' not in columns:
        cursor.execute("ALTER TABLE events ADD COLUMN source TEXT DEFAULT 'unknown'")
    if 'tags' not in columns:
        cursor.execute("ALTER TABLE events ADD COLUMN tags TEXT DEFAULT ''")
