import sys
import os
import argparse
import json

# Ensure we can import from the parent directory (scripts package)
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import scripts.db as db
import scripts.core as core

if __name__ == "__main__":
    db.init_db()
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
    update_parser.add_argument("--status", choices=['active', 'paused', 'completed', 'failed'])
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
    log_parser.add_argument("--source", default="unknown", help="Source of the event (e.g. agent name)")
    log_parser.add_argument("--tags", default="", help="Comma-separated tags for the event")

    # Status
    status_parser = subparsers.add_parser("status")
    status_parser.add_argument("--id", required=True)
    status_parser.add_argument("--filter-tag", help="Filter events by tag")

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
        core.start_project(args.id, args.name or args.id, args.objective, args.priority)
    elif args.command == "list":
        projects = core.list_projects()
        if not projects:
            print("No projects found.")
        for p in projects:
            print(f"[{p[3].upper()}] (P{p[5]}) {p[0]}: {p[1]} - {p[2]} ({p[4]})")
    elif args.command == "update":
        core.update_status(args.id, args.status, args.priority)
    elif args.command == "cache":
        if args.set_result:
            core.log_search(args.query, json.loads(args.set_result))
            print(f"Cached result for: {args.query}")
        else:
            result = core.check_search(args.query)
            if result:
                print(json.dumps(result, indent=2))
            else:
                print("No cached result found.")
    elif args.command == "log":
        core.log_event(args.id, args.type, args.step, json.loads(args.payload), args.conf, args.source, args.tags)
        print(f"Logged {args.type} for {args.id} (conf: {args.conf}, source: {args.source}, tags: {args.tags})")
    elif args.command == "status":
        status = core.get_status(args.id, tag_filter=args.filter_tag)
        if not status:
            print(f"Project '{args.id}' not found.")
        else:
            p = status['project']
            print(f"\n--- Project: {p[1]} ({p[0]}) ---")
            print(f"Status: {p[3].upper()}")
            print(f"Objective: {p[2]}")
            print(f"Created: {p[4]}")
            print("\nRecent Events" + (f" (Filtered by tag: {args.filter_tag})" if args.filter_tag else "") + ":")
            for e in status['recent_events']:
                print(f"  [{e[5]}] {e[0]} (Step {e[1]}) [Src: {e[4]}, Conf: {e[3]}, Tags: {e[6]}]: {e[2]}")
            
            insights = core.get_insights(args.id)
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
                core.add_insight(args.id, args.title, args.content, args.url, args.tags)
                print(f"Added insight to project '{args.id}'.")
        else:
            insights = core.get_insights(args.id, tag_filter=args.filter_tag)
            if not insights:
                print("No insights found" + (f" with tag '{args.filter_tag}'" if args.filter_tag else ""))
            for i in insights:
                print(f"[{i[4]}] {i[0]}\nContent: {i[1]}\nSource: {i[2]}\nTags: {i[3]}\n")
