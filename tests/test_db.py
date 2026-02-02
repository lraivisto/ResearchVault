import scripts.db as db
import pytest
import sqlite3

def test_init_db_schema(db_conn):
    """
    Test that init_db creates all required tables with correct columns.
    """
    c = db_conn.cursor()
    
    # Check Projects table
    c.execute("PRAGMA table_info(projects)")
    columns = {r[1] for r in c.fetchall()}
    assert "priority" in columns
    assert "status" in columns
    
    # Check Events table
    c.execute("PRAGMA table_info(events)")
    columns = {r[1] for r in c.fetchall()}
    assert "confidence" in columns
    assert "source" in columns
    assert "tags" in columns

def test_migrations_are_idempotent(db_conn):
    """
    Test that running init_db (and thus migrations) multiple times is safe.
    """
    # db_conn fixture ALREADY runs init_db once.
    # Run it again to ensure no error.
    try:
        db.init_db()
    except Exception as e:
        pytest.fail(f"init_db raised exception on re-run: {e}")
