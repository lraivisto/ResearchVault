
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, List
import scripts.core as core
import scripts.db as db

router = APIRouter()

class MissionRequest(BaseModel):
    project_id: str
    finding_id: str
    mission_type: str = "SEARCH" # SEARCH, REFUTE, EXPAND
    query: Optional[str] = None

class WatchTargetRequest(BaseModel):
    project_id: str
    target: str
    target_type: str = "query" # url or query
    tags: Optional[str] = ""

@router.post("/missions")
def create_mission(req: MissionRequest):
    """
    Manually dispatch a verification mission for a finding.
    """
    try:
        # We need to construct the mission manually as core.plan_verification_missions is bulk
        # But we can reuse the logic key parts.
        
        # 1. Resolve finding to get context if query is missing
        if not req.query:
             # Fetch finding content to generate query (simplified)
            conn = db.get_connection()
            c = conn.cursor()
            c.execute("SELECT title FROM findings WHERE id=?", (req.finding_id,))
            row = c.fetchone()
            conn.close()
            if not row:
                raise HTTPException(status_code=404, detail="Finding not found")
            req.query = row[0]

        # 2. Insert Mission directly using core DB logic (or custom wrapper)
        # Since core.plan_verification_missions is a bit high-level, we'll implement a 
        # direct insert here to be precise, or better yet, verify if core has a single-mission function.
        # It doesn't seem to have a public `add_mission` function, so we'll use SQL directly 
        # following the pattern in core.plan_verification_missions.
        
        # ...Or we can just rely on the user to provide a query and use a stripped down version.
        # Let's add a helper in this router for now.
        
        import uuid
        import hashlib
        from datetime import datetime

        mission_id = f"mis_{uuid.uuid4().hex[:10]}"
        qhash = core._query_hash(req.query)
        # Placeholder dedup - simple timestamp based to allow multiple runs
        dedup_hash = hashlib.sha256(f"{mission_id}".encode()).hexdigest() 
        
        conn = db.get_connection()
        c = conn.cursor()
        now = datetime.now().isoformat()
        
        # Resolve branch (default main for now, needs frontend support for branches)
        branch_id = core.resolve_branch_id(req.project_id, "main")

        c.execute(
            """INSERT INTO verification_missions
               (id, project_id, branch_id, finding_id, mission_type, query, query_hash,
                question, rationale, status, priority, result_meta, last_error,
                created_at, updated_at, completed_at, dedup_hash)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                mission_id,
                req.project_id,
                branch_id,
                req.finding_id,
                req.mission_type,
                req.query,
                qhash,
                f"Manual dispatch: {req.query}",
                "User initiated via Portal",
                "open",
                100, # High priority
                "",
                "",
                now,
                now,
                None,
                dedup_hash,
            ),
        )
        conn.commit()
        conn.close()
        
        core.log_event(
            req.project_id,
            "MISSION",
            "dispatch",
            {"mission_id": mission_id, "type": req.mission_type},
            source="portal"
        )
        
        return {"status": "dispatched", "mission_id": mission_id}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/watch")
def add_watch_target(req: WatchTargetRequest):
    """
    Add a new watch target (Scope Expansion).
    """
    try:
        target_id = core.add_watch_target(
            req.project_id,
            req.target_type,
            req.target,
            tags=req.tags
        )
        return {"status": "added", "target_id": target_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
