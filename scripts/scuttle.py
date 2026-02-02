import subprocess
import json
import argparse
import sys
import os

# Ensure we can import from the parent directory (scripts package)
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.append(PROJECT_ROOT)

import scripts.core as core

def scuttle_scan(project_id, query, source_data, source_type):
    """
    Logs a scan result from a specific source with appropriate confidence.
    """
    confidence = 0.95 # Default
    tags = [source_type, "scan"]

    if source_type.lower() == "moltbook":
        confidence = 0.55 # Suspicion Protocol
        tags.append("unverified")
    elif source_type.lower() == "x":
        confidence = 0.85
        tags.append("real-time")
    elif source_type.lower() == "reddit":
        confidence = 0.80
        tags.append("discussion")

    core.log_event(
        project_id=project_id,
        event_type="SCAN_RESULT",
        step=0,
        payload={"query": query, "data": source_data},
        confidence=confidence,
        source=source_type,
        tags=",".join(tags)
    )
    print(f"✅ Scuttled {source_type} data for {project_id} (Confidence: {confidence})")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Multi-source Scuttle Helper")
    parser.add_argument("--id", required=True, help="Project ID")
    parser.add_argument("--query", required=True, help="Original search query")
    parser.add_argument("--source", required=True, choices=["X", "Reddit", "Moltbook"], help="Data source")
    parser.add_argument("--data", required=True, help="The finding/data string")

    args = parser.parse_args()
    scuttle_scan(args.id, args.query, args.data, args.source)
