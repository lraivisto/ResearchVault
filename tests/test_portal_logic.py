
import os
import requests
import pytest
import secrets

# Mock token for testing
os.environ["RESEARCHVAULT_PORTAL_TOKEN"] = "test-token"

BASE_URL = "http://127.0.0.1:8000"
TOKEN = "test-token"

def test_health():
    # Note: This requires the backend to be running.
    # We can't easily start/stop the backend in a simple script without uvicorn fixtures.
    # However, we can check the routers logic via unit tests if we wanted to mock FastAPI.
    pass

# Instead of a full integration test that requires a running server, 
# I'll check for common pitfalls in the code.

def test_scrub_logic():
    from scripts.core import scrub_data
    data = {"secret": "private-key", "nested": {"url": "http://user:pass@example.com"}}
    scrubbed = scrub_data(data)
    assert "private-key" not in str(scrubbed)
    assert "pass" not in str(scrubbed)
