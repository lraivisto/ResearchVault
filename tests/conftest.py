import pytest
import sqlite3
import os
import scripts.db as db

@pytest.fixture
def db_conn(monkeypatch):
    """
    Creates an in-memory SQLite database for testing.
    Monkeypatches scripts.db.get_connection to return this connection.
    """
    # Create in-memory connection
    conn = sqlite3.connect(":memory:")
    
    # Mock the get_connection function in db module/other modules
    def mock_get_connection():
        return conn
        
    monkeypatch.setattr(db, "get_connection", mock_get_connection)
    
    # Initialize schema
    db.init_db()
    
    yield conn
    
    conn.close()

@pytest.fixture
def reset_db(db_conn):
    """
    Fixture to ensure DB is clean. 
    (In-memory DB with yield teardown usually handles this, 
    but this provides a clean slate point if needed).
    """
    cursor = db_conn.cursor()
    cursor.execute("DELETE FROM projects")
    cursor.execute("DELETE FROM events")
    cursor.execute("DELETE FROM search_cache")
    cursor.execute("DELETE FROM insights")
    db_conn.commit()
    return db_conn
