
from fastapi import APIRouter, Query
from typing import List, Optional
import scripts.db as db
import json

router = APIRouter()

@router.get("/graph")
def get_graph_data(project_id: Optional[str] = None):
    """
    Returns nodes (findings) and links for the force-directed graph.
    """
    conn = db.get_connection()
    c = conn.cursor()
    
    # 1. Fetch Nodes (Findings)
    # If project_id is provided, filter by it.
    query_findings = "SELECT id, title, content, confidence, tags, created_at, project_id FROM findings"
    params_findings = []
    
    if project_id:
        query_findings += " WHERE project_id=?"
        params_findings.append(project_id)
        
    c.execute(query_findings, params_findings)
    findings = c.fetchall()
    
    nodes = []
    finding_ids = set()
    
    for f in findings:
        f_id, title, content, confidence, tags, created_at, p_id = f
        finding_ids.add(f_id)
        nodes.append({
            "id": f_id,
            "label": title,
            "content": content,
            "group": "finding",
            "val": (confidence or 0.5) * 10,  # Size based on confidence
            "tags": (tags or "").split(","),
            "project_id": p_id
        })

    # 2. Fetch Links
    # We only want links where both source and target exist in our node set
    c.execute("SELECT source_id, target_id, link_type, metadata FROM links")
    all_links = c.fetchall()
    
    links = []
    for l in all_links:
        source, target, l_type, meta = l
        if source in finding_ids and target in finding_ids:
            links.append({
                "source": source,
                "target": target,
                "type": l_type,
                "color": "#bd00ff" if l_type == "SYNTHESIS_SIMILARITY" else "#00f0ff" # Purple for synthesis, Cyan for manual
            })
            
    conn.close()
    
    return {
        "nodes": nodes,
        "links": links
    }
