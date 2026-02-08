
import asyncio
import json
from datetime import datetime
from typing import AsyncGenerator

from fastapi import APIRouter, Depends
from sse_starlette.sse import EventSourceResponse

import scripts.db as db
from portal.backend.app.auth import require_portal_token
from scripts.core import scrub_data

router = APIRouter(dependencies=[Depends(require_portal_token)])

# Global state isn't ideal for scale, but perfect for a single-user local app.
# We'll use a polling approach per connection for simplicity and robustness with SQLite.

async def event_generator(project_id: Optional[str] = None, last_id: int = 0) -> AsyncGenerator[dict, None]:
    """
    Polls the SQLite database for new events and yields them as SSE messages.
    """
    current_id = last_id
    
    # Initial "pulse" to confirm connection
    yield {
        "event": "pulse",
        "data": json.dumps({"status": "connected", "timestamp": datetime.now().isoformat()})
    }

    while True:
        try:
            conn = db.get_connection()
            c = conn.cursor()
            
            # Fetch events newer than current_id
            if project_id:
                c.execute(
                    "SELECT id, event_type, step, payload, confidence, source, tags, timestamp FROM events WHERE id > ? AND project_id = ? ORDER BY id ASC LIMIT 50",
                    (current_id, project_id)
                )
            else:
                c.execute(
                    "SELECT id, event_type, step, payload, confidence, source, tags, timestamp FROM events WHERE id > ? ORDER BY id ASC LIMIT 50",
                    (current_id,)
                )
            rows = c.fetchall()
            conn.close()

            if rows:
                for row in rows:
                    event_id, event_type, step, payload, confidence, source, tags, timestamp = row
                    current_id = event_id
                    
                    # Construct event object
                    event_data = {
                        "id": event_id,
                        "type": event_type,
                        "step": step,
                        "payload": json.loads(payload) if payload else {},  # JSON string in DB
                        "confidence": confidence,
                        "source": source,
                        "tags": tags,
                        "timestamp": timestamp,
                    }

                    # Scrub before sending to the browser.
                    event_data = scrub_data(event_data)

                    # Yield SSE event
                    yield {
                        "event": "log",
                        "id": str(event_id),
                        "data": json.dumps(event_data),
                    }
                    
                    # If this event suggests a graph update (e.g., finding added), send a specific signal
                    if event_type in ("INGEST", "SYNTHESIS", "LINK", "ARTIFACT"):
                         yield {
                            "event": "graph_update",
                            "data": json.dumps({"reason": event_type})
                        }
            else:
                # Heartbeat to keep connection alive
                yield {
                    "event": "pulse",
                    "data": json.dumps({"timestamp": datetime.now().isoformat()})
                }

        except Exception as e:
            yield {
                "event": "error",
                "data": json.dumps(scrub_data({"error": str(e)})),
            }
            await asyncio.sleep(5)  # Backoff on error

        await asyncio.sleep(0.5) # Poll interval

@router.get("/stream")
async def stream_events(project_id: Optional[str] = None, last_event_id: int = 0):
    return EventSourceResponse(event_generator(project_id, last_event_id))
