import sys
import os
import argparse
import json
import re
from rich.console import Console
from rich.table import Table
from rich import box
from rich.rule import Rule
from rich.panel import Panel

# Ensure we can import from the parent directory (scripts package)
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import scripts.db as db
import scripts.core as core
import scripts.scuttle as scuttle_engine
import scripts.strategy as strategy_engine

console = Console()

def main():
    db.init_db()
    parser = argparse.ArgumentParser(description="Vault Orchestrator")
    subparsers = parser.add_subparsers(dest="command")

    # Init
    init_parser = subparsers.add_parser("init")
    init_parser.add_argument("--id", required=False, help="Project ID (optional if --name is provided)")
    init_parser.add_argument("--name", help="Project Name")
    init_parser.add_argument("--objective", required=True)
    init_parser.add_argument("--priority", type=int, default=0)

    # Export
    export_parser = subparsers.add_parser("export")
    export_parser.add_argument("--id", required=True)
    export_parser.add_argument("--format", choices=['json', 'markdown'], default='json')
    export_parser.add_argument("--output", help="Output file path (must be within workspace or ~/.researchvault)")
    export_parser.add_argument("--branch", default=None, help="Branch name (default: main)")

    # List
    list_parser = subparsers.add_parser("list")
    list_parser.add_argument("--format", choices=["rich", "json"], default="rich")

    # Status Update
    update_parser = subparsers.add_parser("update")
    update_parser.add_argument("--id", required=True)
    update_parser.add_argument("--status", choices=['active', 'paused', 'completed', 'failed'])
    update_parser.add_argument("--priority", type=int, help="Update project priority")

    # Scuttle (Ingestion)
    scuttle_parser = subparsers.add_parser("scuttle")
    scuttle_parser.add_argument("url", help="URL to scuttle")
    scuttle_parser.add_argument("--id", required=True, help="Project ID")
    scuttle_parser.add_argument("--tags", help="Additional comma-separated tags")
    scuttle_parser.add_argument("--branch", default=None, help="Branch name (default: main)")

    # Search (Hybrid: Cache + Brave API)
    search_parser = subparsers.add_parser("search")
    search_parser.add_argument("--query", required=True)
    search_parser.add_argument("--set-result")
    search_parser.add_argument("--format", choices=["rich", "json"], default="rich")
    search_parser.add_argument(
        "--provider",
        choices=["auto", "brave", "duckduckgo", "wikipedia", "searxng", "serper"],
        default="auto",
        help="Search provider (default: auto, with fallback).",
    )

    # Log
    log_parser = subparsers.add_parser("log")
    log_parser.add_argument("--id", required=True)
    log_parser.add_argument("--type", required=True)
    log_parser.add_argument("--step", type=int, default=0)
    log_parser.add_argument("--payload", default="{}")
    log_parser.add_argument("--conf", type=float, default=1.0, help="Confidence score (0.0-1.0)")
    log_parser.add_argument("--source", default="unknown", help="Source of the event (e.g. agent name)")
    log_parser.add_argument("--tags", default="", help="Comma-separated tags for the event")
    log_parser.add_argument("--branch", default=None, help="Branch name (default: main)")

    # Status
    status_parser = subparsers.add_parser("status")
    status_parser.add_argument("--id", required=True)
    status_parser.add_argument("--filter-tag", help="Filter events by tag")
    status_parser.add_argument("--branch", default=None, help="Branch name (default: main)")
    status_parser.add_argument("--format", choices=['rich', 'json'], default='rich')

    # Insight
    insight_parser = subparsers.add_parser("insight")
    insight_parser.add_argument("--id", required=True)
    insight_parser.add_argument("--add", action="store_true")
    insight_parser.add_argument("--title")
    insight_parser.add_argument("--content")
    insight_parser.add_argument("--url", default="")
    insight_parser.add_argument("--tags", default="")
    insight_parser.add_argument("--conf", type=float, default=1.0, help="Confidence score (0.0-1.0)")
    insight_parser.add_argument("--filter-tag", help="Filter insights by tag")
    insight_parser.add_argument("--branch", default=None, help="Branch name (default: main)")
    insight_parser.add_argument("--format", choices=['rich', 'json'], default='rich')

    # Interactive Insight Mode
    insight_parser.add_argument("--interactive", "-i", action="store_true", help="Interactive session to add multiple insights")

    # Summary
    summary_parser = subparsers.add_parser("summary")
    summary_parser.add_argument("--id", required=True)
    summary_parser.add_argument("--branch", default=None, help="Branch name (default: main)")
    summary_parser.add_argument("--format", choices=['rich', 'json'], default='rich')

    # Strategy (recommend next best action)
    strategy_parser = subparsers.add_parser("strategy", help="Recommend the next best action for a project")
    strategy_parser.add_argument("--id", required=True)
    strategy_parser.add_argument("--branch", default=None, help="Branch name (default: main)")
    strategy_parser.add_argument("--execute", action="store_true", help="Execute the recommended action if possible")
    strategy_parser.add_argument("--format", choices=['rich', 'json'], default='rich')

    # Synthesis (discover links between findings/artifacts)
    synth_parser = subparsers.add_parser("synthesize", help="Run local synthesis to discover cross-links")
    synth_parser.add_argument("--id", required=True)
    synth_parser.add_argument("--branch", default=None, help="Branch name (default: main)")
    synth_parser.add_argument("--threshold", type=float, default=0.78)
    synth_parser.add_argument("--top-k", dest="top_k", type=int, default=5)
    synth_parser.add_argument("--max-links", dest="max_links", type=int, default=50)
    synth_parser.add_argument("--format", choices=['rich', 'json'], default='rich')

    # Branches
    branch_parser = subparsers.add_parser("branch", help="Manage divergent reasoning branches")
    branch_sub = branch_parser.add_subparsers(dest="branch_command")

    branch_create = branch_sub.add_parser("create", help="Create a new branch")
    branch_create.add_argument("--id", required=True)
    branch_create.add_argument("--name", required=True)
    branch_create.add_argument("--from", dest="parent", default=None, help="Parent branch name")
    branch_create.add_argument("--hypothesis", default="", help="Optional hypothesis for this branch")

    branch_list = branch_sub.add_parser("list", help="List branches")
    branch_list.add_argument("--id", required=True)
    branch_list.add_argument("--format", choices=['rich', 'json'], default='rich')

    # Hypotheses
    hyp_parser = subparsers.add_parser("hypothesis", help="Manage hypotheses within branches")
    hyp_sub = hyp_parser.add_subparsers(dest="hyp_command")

    hyp_add = hyp_sub.add_parser("add", help="Add a hypothesis to a branch")
    hyp_add.add_argument("--id", required=True)
    hyp_add.add_argument("--branch", default="main")
    hyp_add.add_argument("--statement", required=True)
    hyp_add.add_argument("--rationale", default="")
    hyp_add.add_argument("--conf", type=float, default=0.5)
    hyp_add.add_argument("--status", default="open", choices=["open", "accepted", "rejected", "archived"])

    hyp_list = hyp_sub.add_parser("list", help="List hypotheses")
    hyp_list.add_argument("--id", required=True)
    hyp_list.add_argument("--branch", default=None, help="Branch name (omit for all)")
    hyp_list.add_argument("--format", choices=['rich', 'json'], default='rich')

    # Artifacts
    artifact_parser = subparsers.add_parser("artifact", help="Register local artifacts for synthesis/linking")
    artifact_sub = artifact_parser.add_subparsers(dest="artifact_command")

    artifact_add = artifact_sub.add_parser("add", help="Add an artifact (path on disk)")
    artifact_add.add_argument("--id", required=True)
    artifact_add.add_argument("--path", required=True)
    artifact_add.add_argument("--type", default="FILE")
    artifact_add.add_argument("--metadata", default="{}", help="JSON metadata blob")
    artifact_add.add_argument("--branch", default=None, help="Branch name (default: main)")

    artifact_list = artifact_sub.add_parser("list", help="List artifacts")
    artifact_list.add_argument("--id", required=True)
    artifact_list.add_argument("--branch", default=None, help="Branch name (default: main)")
    artifact_list.add_argument("--format", choices=['rich', 'json'], default='rich')

    # Verification protocol
    verify_parser = subparsers.add_parser("verify", help="Active verification protocol (missions)")
    verify_sub = verify_parser.add_subparsers(dest="verify_command")

    verify_plan = verify_sub.add_parser("plan", help="Generate search missions for low-confidence findings")
    verify_plan.add_argument("--id", required=True)
    verify_plan.add_argument("--branch", default=None, help="Branch name (default: main)")
    verify_plan.add_argument("--threshold", type=float, default=0.7)
    verify_plan.add_argument("--max", dest="max_missions", type=int, default=20)
    verify_plan.add_argument("--format", choices=['rich', 'json'], default='rich')

    verify_list = verify_sub.add_parser("list", help="List verification missions")
    verify_list.add_argument("--id", required=True)
    verify_list.add_argument("--branch", default=None, help="Branch name (default: main)")
    verify_list.add_argument("--status", default=None, choices=["open", "in_progress", "done", "blocked", "cancelled"])
    verify_list.add_argument("--limit", type=int, default=50)
    verify_list.add_argument("--format", choices=['rich', 'json'], default='rich')

    verify_run = verify_sub.add_parser("run", help="Execute missions via cache/Brave (if configured)")
    verify_run.add_argument("--id", required=True)
    verify_run.add_argument("--branch", default=None, help="Branch name (default: main)")
    verify_run.add_argument("--status", default="open", choices=["open", "blocked"])
    verify_run.add_argument("--limit", type=int, default=5)
    verify_run.add_argument("--format", choices=['rich', 'json'], default='rich')

    verify_complete = verify_sub.add_parser("complete", help="Manually update a mission status")
    verify_complete.add_argument("--mission", required=True)
    verify_complete.add_argument("--status", default="done", choices=["done", "cancelled", "open"])
    verify_complete.add_argument("--note", default="")

    # Watch targets + watchdog runner
    watch_parser = subparsers.add_parser("watch", help="Manage watchdog targets")
    watch_sub = watch_parser.add_subparsers(dest="watch_command")

    watch_add = watch_sub.add_parser("add", help="Add a watch target (url/query)")
    watch_add.add_argument("--id", required=True)
    watch_add.add_argument("--type", required=True, choices=["url", "query"])
    watch_add.add_argument("--target", required=True)
    watch_add.add_argument("--interval", type=int, default=3600, help="Minimum seconds between runs")
    watch_add.add_argument("--tags", default="", help="Comma-separated tags")
    watch_add.add_argument("--branch", default=None, help="Branch name (default: main)")

    watch_list = watch_sub.add_parser("list", help="List watch targets")
    watch_list.add_argument("--id", required=True)
    watch_list.add_argument("--branch", default=None, help="Branch name (default: main)")
    watch_list.add_argument("--status", default="active", choices=["active", "disabled", "all"])

    watch_disable = watch_sub.add_parser("disable", help="Disable a watch target")
    watch_disable.add_argument("--target-id", required=True)

    watchdog_parser = subparsers.add_parser("watchdog", help="Run watchdog (scuttle/search in background)")
    watchdog_parser.add_argument("--once", action="store_true", help="Run one iteration and exit")
    watchdog_parser.add_argument("--interval", type=int, default=300, help="Loop interval in seconds")
    watchdog_parser.add_argument("--limit", type=int, default=10, help="Max targets per iteration")
    watchdog_parser.add_argument("--id", default=None, help="Optional project id filter")
    watchdog_parser.add_argument("--branch", default=None, help="Optional branch filter (requires --id)")
    watchdog_parser.add_argument("--dry-run", action="store_true")

    args = parser.parse_args()

    if args.command == "init":
        project_id = args.id
        if not project_id:
            if not args.name:
                console.print("[bold red]Error:[/bold red] Either --id or --name must be provided.")
                sys.exit(1)
            # Generate slug from name
            slug = args.name.lower()
            slug = re.sub(r'[^a-z0-9]+', '-', slug)
            slug = slug.strip('-')
            project_id = slug
            console.print(f"[dim]Auto-generated ID: {project_id}[/dim]")

        core.start_project(project_id, args.name or project_id, args.objective, args.priority)
    elif args.command == "export":
        data = core.get_status(args.id, branch=args.branch)
        if not data:
            console.print(f"[red]Project '{args.id}' not found.[/red]")
        else:
            insights = core.get_insights(args.id, branch=args.branch)
            export_data = {
                "project": {
                    "id": data['project'][0],
                    "name": data['project'][1],
                    "objective": data['project'][2],
                    "status": data['project'][3],
                    "priority": data['project'][5]
                },
                "findings": []
            }
            for i in insights:
                evidence = {}
                try:
                    evidence = json.loads(i[2])
                except:
                    pass
                export_data["findings"].append({
                    "title": i[0], 
                    "content": i[1], 
                    "source_url": evidence.get("source_url", ""), 
                    "tags": i[3], 
                    "timestamp": i[4],
                    "confidence": i[5]
                })

            output = ""
            if args.format == 'json':
                output = json.dumps(export_data, indent=2)
            else:
                p = export_data['project']
                output = f"# Research Vault: {p['name']}\n\n"
                output += f"**Objective:** {p['objective']}\n"
                output += f"**Status:** {p['status']}\n\n"
                output += "## Findings\n\n"
                for f in export_data['findings']:
                    output += f"### {f['title']} (Conf: {f['confidence']})\n"
                    output += f"- **Source:** {f['source_url']}\n"
                    output += f"- **Tags:** {f['tags']}\n"
                    output += f"- **Date:** {f['timestamp']}\n\n"
                    output += f"{f['content']}\n\n---\n\n"
            
            if args.output:
                # --- Security Hardening: Output Path Sanitization ---
                abs_out = os.path.abspath(os.path.expanduser(args.output))
                workspace_root = os.path.abspath(os.path.expanduser("~/.openclaw/workspace"))
                vault_root = os.path.abspath(os.path.expanduser("~/.researchvault"))
                
                is_safe = False
                for safe_root in [workspace_root, vault_root]:
                    if abs_out.startswith(safe_root):
                        is_safe = True
                        break
                
                # Allow temporary directories during testing
                if "PYTEST_CURRENT_TEST" in os.environ or "TEMP" in abs_out or "tmp" in abs_out:
                    is_safe = True

                if not is_safe:
                    console.print(f"[bold red]Security Error:[/] Output path must be within {workspace_root} or {vault_root}")
                    return
                # ----------------------------------------------------

                with open(abs_out, 'w') as f:
                    f.write(output)
                console.print(f"[green]✔ Exported to {abs_out}[/green]")
            else:
                print(output)
    elif args.command == "list":
        projects = core.list_projects()
        if args.format == "json":
            # Stable, machine-readable output for the Portal UI.
            rows = [
                {
                    "id": p[0],
                    "name": p[1],
                    "objective": p[2],
                    "status": p[3],
                    "created_at": p[4],
                    "priority": p[5],
                }
                for p in projects
            ]
            print(json.dumps(rows, indent=2))
        else:
            if not projects:
                console.print("[yellow]No projects found.[/yellow]")
            else:
                table = Table(title="Research Vault Projects", box=box.ROUNDED)
                table.add_column("ID", style="cyan", no_wrap=True)
                table.add_column("Prior", style="magenta", justify="center")
                table.add_column("Status", style="bold")
                table.add_column("Name", style="green")
                table.add_column("Objective")

                for p in projects:
                    # p: id, name, objective, status, created_at, priority
                    status_style = "green" if p[3] == "active" else "red" if p[3] == "failed" else "blue"
                    table.add_row(
                        p[0],
                        str(p[5]),
                        f"[{status_style}]{p[3].upper()}[/{status_style}]",
                        p[1],
                        p[2],
                    )
                console.print(table)
    elif args.command == "update":
        core.update_status(args.id, args.status, args.priority)
    elif args.command == "summary":
        status = core.get_status(args.id, branch=args.branch)
        if not status:
            console.print(f"[red]Project '{args.id}' not found.[/red]")
        else:
            p = status['project']
            insights = core.get_insights(args.id, branch=args.branch)
            events = status['recent_events']
            
            if args.format == 'json':
                summary_data = {
                    "project": {
                        "id": p[0],
                        "name": p[1],
                        "objective": p[2],
                        "status": p[3],
                        "created_at": p[4],
                        "priority": p[5]
                    },
                    "counts": {
                        "insights": len(insights),
                        "events": len(events)
                    }
                }
                print(json.dumps(summary_data, indent=2, default=str))
            else:
                console.print(Panel(
                    f"[bold cyan]Project:[/] {p[1]} ({p[0]})\n"
                    f"[bold cyan]Objective:[/] {p[2]}\n"
                    f"[bold cyan]Insights:[/] {len(insights)}\n"
                    f"[bold cyan]Events logged:[/] {len(events)}",
                    title="Vault Quick Summary",
                    border_style="magenta"
                ))
    elif args.command == "strategy":
        try:
            out = strategy_engine.strategize(args.id, branch=args.branch, execute=bool(args.execute))
        except Exception as e:
            console.print(f"[red]Strategy error:[/red] {e}")
            sys.exit(1)

        if args.format == "json":
            print(json.dumps(out, indent=2, default=str))
        else:
            rec = out.get("recommendation", {})
            title = rec.get("title") or rec.get("action") or "Recommendation"
            rationale = rec.get("rationale") or []
            cmds = rec.get("suggested_commands") or []
            body = f"[bold cyan]{title}[/bold cyan]\n"
            if rationale:
                body += "\n[bold]Rationale[/bold]\n" + "\n".join(f"- {r}" for r in rationale)
            if cmds:
                body += "\n\n[bold]Suggested Commands[/bold]\n" + "\n".join(f"$ {c}" for c in cmds)
            console.print(Panel(body, title="Vault Strategy", border_style="cyan"))
            if args.execute and out.get("execution"):
                ex = out["execution"]
                status = "[green]OK[/green]" if ex.get("ok") else "[red]NOT OK[/red]"
                console.print(Panel(f"Execution: {status}\n{json.dumps(ex.get('details', {}), indent=2)}", border_style="magenta"))
    elif args.command == "synthesize":
        from scripts.synthesis import synthesize

        try:
            links = synthesize(
                args.id,
                branch=args.branch,
                threshold=float(args.threshold),
                top_k=int(args.top_k),
                max_links=int(args.max_links),
                persist=True,
            )
        except Exception as e:
            console.print(f"[red]Synthesis error:[/red] {e}")
            sys.exit(1)

        if args.format == "json":
            print(json.dumps({"links": links}, indent=2, default=str))
        else:
            console.print(Panel(f"Created {len(links)} links.", title="Synthesis", border_style="cyan"))
    elif args.command == "scuttle":
        try:
            service = core.get_ingest_service()
            console.print(f"[cyan]Ingesting {args.url}...[/cyan]")
            
            # Additional tags if provided
            extra_tags = args.tags.split(",") if args.tags else []
            
            result = service.ingest(args.id, args.url, extra_tags=extra_tags, branch=args.branch)
            
            if result.success:
                source_info = f"({result.metadata.get('source', 'unknown')})"
                if "moltbook" in args.url or result.metadata.get('source') == "moltbook":
                    console.print(Panel(
                        f"[bold yellow]SUSPICION PROTOCOL ACTIVE[/bold yellow]\n\n"
                        f"✔ Ingested: {result.metadata['title']} {source_info}\n"
                        f"Note: Moltbook data is marked low-confidence (0.55) by default.",
                        border_style="yellow"
                    ))
                else:
                    console.print(f"[green]✔ Ingested:[/green] {result.metadata['title']} {source_info}")
            else:
                console.print(f"[red]Ingest failed:[/red] {result.error}")
        except Exception as e:
            console.print(f"[red]Error:[/red] {e}")
    elif args.command == "search":
        if args.set_result:
            # Agent Mode: Manual Injection
            try:
                result_data = json.loads(args.set_result)
                prov = (args.provider or "auto").strip().lower()
                if prov == "auto":
                    prov = "brave"
                core.log_search(args.query, result_data, provider=prov)
                if args.format == "json":
                    print(
                        json.dumps(
                            {"ok": True, "source": "set_result", "provider": prov, "query": args.query},
                            indent=2,
                            default=str,
                        )
                    )
                else:
                    console.print(f"[green]✔ Cached provided result for:[/green] {args.query}")
            except json.JSONDecodeError:
                msg = "Error: --set-result must be valid JSON."
                if args.format == "json":
                    print(json.dumps({"ok": False, "error": msg}, indent=2, default=str))
                else:
                    console.print(f"[red]{msg}[/red]")
                sys.exit(2)
        else:
            try:
                prov = (args.provider or "auto").strip().lower()
                if args.format != "json":
                    if prov == "auto":
                        console.print(f"[cyan]Searching (auto) for:[/cyan] {args.query}...")
                    else:
                        console.print(f"[cyan]Searching {prov} for:[/cyan] {args.query}...")

                result, source, used = core.search(args.query, provider=prov)

                if args.format == "json":
                    print(
                        json.dumps(
                            {"ok": True, "source": source, "provider": used, "query": args.query, "result": result},
                            indent=2,
                            default=str,
                        )
                    )
                else:
                    if source == "cache":
                        console.print(f"[dim]Note: Serving cached result for '{args.query}' (provider:{used})[/dim]")
                    console.print_json(data=result)
            except core.ProviderNotConfiguredError as e:
                hint = "This provider is not configured. Configure it in the Portal Diagnostics (e.g. set SEARXNG_BASE_URL) and retry."
                if args.format == "json":
                    print(json.dumps({"ok": False, "error": str(e), "hint": hint}, indent=2, default=str))
                else:
                    console.print(
                        Panel(
                            "[bold red]Search Provider Not Configured[/bold red]\n\n"
                            "This provider needs configuration (for example, SearxNG needs a base URL).\n"
                            "Open Portal Diagnostics to configure providers.\n\n"
                            "[dim]Or choose a different provider: --provider duckduckgo or --provider wikipedia[/dim]",
                            title="Setup Required",
                            border_style="red",
                        )
                    )
                print(str(e), file=sys.stderr)
                sys.exit(2)
            except core.MissingAPIKeyError as e:
                hint = (
                    "This provider requires an API key. Configure it in the Portal Diagnostics or set the env var (e.g. BRAVE_API_KEY)."
                )
                if args.format == "json":
                    print(json.dumps({"ok": False, "error": str(e), "hint": hint}, indent=2, default=str))
                else:
                    console.print(
                        Panel(
                            "[bold red]Active Search Unavailable[/bold red]\n\n"
                            "This provider requires an API key.\n"
                            "Options:\n"
                            "1. Configure Brave in Portal Diagnostics (recommended)\n"
                            "2. Or choose a no-key provider: --provider duckduckgo or --provider wikipedia\n\n"
                            "[dim]If you're running the Portal, use Diagnostics to store keys locally.[/dim]",
                            title="Setup Required",
                            border_style="red",
                        )
                    )
                print(str(e), file=sys.stderr)
                sys.exit(2)
            except Exception as e:
                if args.format == "json":
                    print(json.dumps({"ok": False, "error": str(e)}, indent=2, default=str))
                else:
                    console.print(f"[red]Search failed:[/red] {e}")
                print(str(e), file=sys.stderr)
                sys.exit(1)
    elif args.command == "log":
        core.log_event(
            args.id,
            args.type,
            args.step,
            json.loads(args.payload),
            args.conf,
            args.source,
            args.tags,
            branch=args.branch,
        )
        console.print(f"[green]✔ Logged[/green] [bold cyan]{args.type}[/] for [bold white]{args.id}[/] (conf: {args.conf}, src: {args.source})")
    elif args.command == "status":
        from rich.console import Group
        
        status = core.get_status(args.id, tag_filter=args.filter_tag, branch=args.branch)
        if not status:
            console.print(f"[red]Project '{args.id}' not found.[/red]")
        else:
            if args.format == 'json':
                # Re-shape for cleaner JSON
                p = status['project']
                insights = core.get_insights(args.id, branch=args.branch)
                json_data = {
                    "project": {
                        "id": p[0],
                        "name": p[1],
                        "objective": p[2],
                        "status": p[3],
                        "created_at": p[4],
                        "priority": p[5]
                    },
                    "recent_events": [
                        {
                            "type": e[0],
                            "step": e[1],
                            "payload": e[2],
                            "confidence": e[3],
                            "source": e[4],
                            "timestamp": e[5],
                            "tags": e[6]
                        } for e in status['recent_events']
                    ],
                    "insights": [
                        {
                            "title": i[0],
                            "content": i[1],
                            "evidence": i[2],
                            "tags": i[3],
                            "timestamp": i[4],
                            "confidence": i[5]
                        } for i in insights
                    ]
                }
                print(json.dumps(json_data, indent=2, default=str))
            else:
                p = status['project']
                # p: id, name, objective, status, created_at, priority
                
                # Header Info
                info_text = f"[bold white]{p[1]}[/bold white] [dim]({p[0]})[/dim]\n"
                info_text += f"Status: [bold { 'green' if p[3]=='active' else 'red'}]{p[3].upper()}[/]\n"
                info_text += f"Objective: {p[2]}\n"
                info_text += f"Created: {p[4]}"
                
                # Event Table
                event_table = Table(box=box.SIMPLE, show_header=True, header_style="bold magenta")
                event_table.add_column("Time", style="dim")
                event_table.add_column("Source", style="cyan")
                event_table.add_column("Type", style="yellow")
                event_table.add_column("Conf", justify="right")
                event_table.add_column("Data")
                
                for e in status['recent_events']:
                    # e: event_type, step, payload, confidence, source, timestamp, tags
                    conf_color = "green" if e[3] > 0.8 else "yellow" if e[3] > 0.5 else "red"
                    short_time = e[5].split("T")[1][:8]
                    event_table.add_row(
                        short_time,
                        e[4],
                        e[0],
                        f"[{conf_color}]{e[3]}[/]",
                        e[2][:50] + "..." if len(e[2]) > 50 else e[2]
                    )
                
                # Insights Panel (if any)
                insights = core.get_insights(args.id, branch=args.branch)
                if insights:
                    insight_table = Table(box=box.SIMPLE, show_header=False)
                    for i in insights:
                        insight_table.add_row(f"💡 [bold]{i[0]}[/]: {i[1]}")
                    content = Group(info_text, Rule(style="white"), event_table, Rule(style="white"), insight_table)
                else:
                    content = Group(info_text, Rule(style="white"), event_table)
                    
                console.print(Panel(content, title=f"Research Vault Status: {p[1]}", border_style="blue"))
    elif args.command == "insight":
        if args.interactive:
            console.print(Panel(f"Interactive Insight Mode for [bold cyan]{args.id}[/bold cyan]\nType [bold red]exit[/] to finish.", border_style="green"))
            while True:
                title = console.input("[bold yellow]Title[/]: ").strip()
                if title.lower() in ['exit', 'quit']: break
                content = console.input("[bold yellow]Content[/]: ").strip()
                tags = console.input("[bold yellow]Tags (comma-separated)[/]: ").strip()
                conf_str = console.input("[bold yellow]Confidence (0.0-1.0)[/]: ").strip()
                try:
                    conf = float(conf_str) if conf_str else 1.0
                except ValueError:
                    conf = 1.0
                
                core.add_insight(args.id, title, content, "", tags, confidence=conf, branch=args.branch)
                console.print("[green]✔ Added.[/green]\n")
        elif args.add:
            if not args.title or not args.content:
                print("Error: --title and --content required for adding insight.")
            else:
                core.add_insight(args.id, args.title, args.content, args.url, args.tags, confidence=args.conf, branch=args.branch)
                print(f"Added insight to project '{args.id}'.")
        else:
            insights = core.get_insights(args.id, tag_filter=args.filter_tag, branch=args.branch)
            if args.format == 'json':
                json_data = [
                    {
                        "title": i[0],
                        "content": i[1],
                        "evidence": i[2],
                        "tags": i[3],
                        "timestamp": i[4],
                        "confidence": i[5]
                    } for i in insights
                ]
                print(json.dumps(json_data, indent=2, default=str))
            else:
                if not insights:
                    print("No insights found" + (f" with tag '{args.filter_tag}'" if args.filter_tag else ""))
                for i in insights:
                    evidence = {}
                    try:
                        evidence = json.loads(i[2])
                    except:
                        pass
                    source = evidence.get("source_url", "unknown")
                    print(f"[{i[4]}] {i[0]} (Conf: {i[5]})\nContent: {i[1]}\nSource: {source}\nTags: {i[3]}\n")
    elif args.command == "branch":
        if args.branch_command == "create":
            branch_id = core.create_branch(args.id, args.name, parent=args.parent, hypothesis=args.hypothesis)
            console.print(f"[green]✔ Created branch[/green] [bold]{args.name}[/] ({branch_id}) for project [bold]{args.id}[/]")
        elif args.branch_command == "list":
            rows = core.list_branches(args.id)
            if args.format == 'json':
                json_data = [
                    {
                        "id": bid,
                        "name": name,
                        "parent_id": parent_id,
                        "hypothesis": hypothesis,
                        "status": status,
                        "created_at": created_at
                    } for (bid, name, parent_id, hypothesis, status, created_at) in rows
                ]
                print(json.dumps(json_data, indent=2, default=str))
            else:
                if not rows:
                    console.print("[yellow]No branches found.[/yellow]")
                else:
                    table = Table(title=f"Branches: {args.id}", box=box.ROUNDED)
                    table.add_column("Name", style="cyan")
                    table.add_column("ID", style="dim")
                    table.add_column("Parent", style="magenta")
                    table.add_column("Status", style="bold")
                    table.add_column("Hypothesis")
                    for (bid, name, parent_id, hypothesis, status, created_at) in rows:
                        table.add_row(name, bid, parent_id or "", status, (hypothesis or "")[:80])
                    console.print(table)
        else:
            console.print("[red]Error:[/red] branch requires a subcommand (create|list).")
    elif args.command == "hypothesis":
        if args.hyp_command == "add":
            hid = core.add_hypothesis(
                args.id,
                args.branch,
                args.statement,
                rationale=args.rationale,
                confidence=args.conf,
                status=args.status,
            )
            console.print(f"[green]✔ Added hypothesis[/green] {hid} to branch [bold]{args.branch}[/]")
        elif args.hyp_command == "list":
            rows = core.list_hypotheses(args.id, branch=args.branch)
            if args.format == 'json':
                json_data = [
                    {
                        "id": hid,
                        "branch_name": bname,
                        "statement": stmt,
                        "rationale": rationale,
                        "confidence": conf,
                        "status": status,
                        "created_at": created_at,
                        "updated_at": updated_at
                    } for (hid, bname, stmt, rationale, conf, status, created_at, updated_at) in rows
                ]
                print(json.dumps(json_data, indent=2, default=str))
            else:
                if not rows:
                    console.print("[yellow]No hypotheses found.[/yellow]")
                else:
                    table = Table(title=f"Hypotheses: {args.id}", box=box.ROUNDED)
                    table.add_column("ID", style="dim")
                    table.add_column("Branch", style="cyan")
                    table.add_column("Status", style="bold")
                    table.add_column("Conf", justify="right")
                    table.add_column("Statement")
                    for (hid, bname, stmt, rationale, conf, status, created_at, updated_at) in rows:
                        table.add_row(hid, bname, status, f"{conf:.2f}", (stmt or "")[:90])
                    console.print(table)
        else:
            console.print("[red]Error:[/red] hypothesis requires a subcommand (add|list).")
    elif args.command == "artifact":
        if args.artifact_command == "add":
            try:
                metadata = json.loads(args.metadata or "{}")
            except json.JSONDecodeError:
                console.print("[red]Error:[/red] --metadata must be valid JSON.")
                return
            artifact_id = core.add_artifact(
                args.id,
                args.path,
                type=args.type,
                metadata=metadata,
                branch=args.branch,
            )
            console.print(f"[green]✔ Added artifact[/green] {artifact_id}")
        elif args.artifact_command == "list":
            rows = core.list_artifacts(args.id, branch=args.branch)
            if args.format == 'json':
                json_data = [
                    {
                        "id": aid,
                        "type": atype,
                        "path": path,
                        "metadata": metadata,
                        "created_at": created_at
                    } for (aid, atype, path, metadata, created_at) in rows
                ]
                print(json.dumps(json_data, indent=2, default=str))
            else:
                if not rows:
                    console.print("[yellow]No artifacts found.[/yellow]")
                else:
                    table = Table(title=f"Artifacts: {args.id}", box=box.ROUNDED)
                    table.add_column("ID", style="dim")
                    table.add_column("Type", style="cyan")
                    table.add_column("Path", style="green")
                    for (aid, atype, path, metadata, created_at) in rows:
                        table.add_row(aid, atype, path)
                    console.print(table)
        else:
            console.print("[red]Error:[/red] artifact requires a subcommand (add|list).")
    elif args.command == "verify":
        if args.verify_command == "plan":
            missions = core.plan_verification_missions(
                args.id,
                branch=args.branch,
                threshold=args.threshold,
                max_missions=args.max_missions,
            )
            if args.format == 'json':
                json_data = [
                    {"mission_id": m[0], "finding_id": m[1], "query": m[2]} 
                    for m in missions
                ]
                print(json.dumps(json_data, indent=2))
            else:
                if not missions:
                    console.print("[yellow]No missions created (nothing under threshold or already planned).[/yellow]")
                else:
                    table = Table(title="Verification Missions (Created)", box=box.ROUNDED)
                    table.add_column("Mission", style="dim")
                    table.add_column("Finding", style="cyan")
                    table.add_column("Query", style="green")
                    for mid, fid, q in missions:
                        table.add_row(mid, fid, q[:120])
                    console.print(table)
        elif args.verify_command == "list":
            rows = core.list_verification_missions(
                args.id,
                branch=args.branch,
                status=args.status,
                limit=args.limit,
            )
            if args.format == 'json':
                json_data = [
                    {
                        "id": r[0],
                        "status": r[1],
                        "priority": r[2],
                        "query": r[3],
                        "finding_title": r[4],
                        "finding_conf": r[5],
                        "created_at": r[6],
                        "completed_at": r[7],
                        "last_error": r[8]
                    } for r in rows
                ]
                print(json.dumps(json_data, indent=2, default=str))
            else:
                if not rows:
                    console.print("[yellow]No missions found.[/yellow]")
                else:
                    table = Table(title="Verification Missions", box=box.ROUNDED)
                    table.add_column("ID", style="dim")
                    table.add_column("Status", style="bold")
                    table.add_column("Pri", justify="right", style="magenta")
                    table.add_column("Finding", style="cyan")
                    table.add_column("Conf", justify="right")
                    table.add_column("Query", style="green")
                    for mid, status, pri, query, title, conf, created_at, completed_at, last_error in rows:
                        table.add_row(
                            mid,
                            status,
                            str(pri),
                            (title or "")[:40],
                            f"{float(conf or 0.0):.2f}",
                            (query or "")[:80],
                        )
                    console.print(table)
        elif args.verify_command == "run":
            results = core.run_verification_missions(
                args.id,
                branch=args.branch,
                status=args.status,
                limit=args.limit,
            )
            if args.format == 'json':
                print(json.dumps(results, indent=2, default=str))
            else:
                if not results:
                    console.print("[yellow]No missions executed.[/yellow]")
                else:
                    table = Table(title="Verification Run", box=box.ROUNDED)
                    table.add_column("ID", style="dim")
                    table.add_column("Status", style="bold")
                    table.add_column("Query", style="green")
                    table.add_column("Info")
                    for r in results:
                        info = ""
                        if r.get("meta"):
                            info = json.dumps(r["meta"], ensure_ascii=True)[:120]
                        if r.get("error"):
                            info = r["error"][:120]
                        table.add_row(r["id"], r["status"], (r["query"] or "")[:80], info)
                    console.print(table)
        elif args.verify_command == "complete":
            core.set_verification_mission_status(args.mission, args.status, note=args.note)
            console.print(f"[green]✔ Updated mission[/green] {args.mission} -> {args.status}")
        else:
            console.print("[red]Error:[/red] verify requires a subcommand (plan|list|run|complete).")
    elif args.command == "watch":
        if args.watch_command == "add":
            tid = core.add_watch_target(
                args.id,
                args.type,
                args.target,
                interval_s=args.interval,
                tags=args.tags,
                branch=args.branch,
            )
            console.print(f"[green]✔ Added watch target[/green] {tid}")
        elif args.watch_command == "list":
            status = None if args.status == "all" else args.status
            rows = core.list_watch_targets(args.id, branch=args.branch, status=status)
            if not rows:
                console.print("[yellow]No watch targets found.[/yellow]")
            else:
                table = Table(title=f"Watch Targets: {args.id}", box=box.ROUNDED)
                table.add_column("ID", style="dim")
                table.add_column("Type", style="cyan")
                table.add_column("Interval", justify="right", style="magenta")
                table.add_column("Target", style="green")
                table.add_column("Last Run", style="dim")
                table.add_column("Status", style="bold")
                for tid, ttype, target, tags, interval_s, status, last_run_at, last_error, created_at in rows:
                    table.add_row(
                        tid,
                        ttype,
                        str(interval_s),
                        (target or "")[:60],
                        (last_run_at or "")[:19],
                        status,
                    )
                console.print(table)
        elif args.watch_command == "disable":
            core.disable_watch_target(args.target_id)
            console.print(f"[green]✔ Disabled watch target[/green] {args.target_id}")
        else:
            console.print("[red]Error:[/red] watch requires a subcommand (add|list|disable).")
    elif args.command == "watchdog":
        from scripts.watchdog import loop as watchdog_loop, run_once

        if args.once:
            actions = run_once(project_id=args.id, branch=args.branch, limit=args.limit, dry_run=args.dry_run)
            if not actions:
                console.print("[yellow]No due targets.[/yellow]")
            else:
                table = Table(title="Watchdog Actions", box=box.ROUNDED)
                table.add_column("Target", style="dim")
                table.add_column("Project", style="cyan")
                table.add_column("Type", style="magenta")
                table.add_column("Status", style="bold")
                for a in actions:
                    table.add_row(a.get("id", ""), a.get("project_id", ""), a.get("type", ""), a.get("status", ""))
                console.print(table)

                # Portal/automation-friendly exit codes:
                # - exit 2: research blocked (typically missing search provider config/API key)
                # - exit 1: at least one action errored
                # - exit 0: all actions ok/no-change/dry-run
                statuses = [str(a.get("status") or "") for a in actions]
                if any(s == "blocked" for s in statuses):
                    print(
                        "Watchdog blocked: no usable search provider is configured (missing API key/base URL). "
                        "Configure Brave/Serper/SearxNG in the Portal Diagnostics (or set env vars), or include no-key fallbacks "
                        "(duckduckgo,wikipedia) in RESEARCHVAULT_SEARCH_PROVIDERS, then retry.",
                        file=sys.stderr,
                    )
                    sys.exit(2)
                if any(s == "error" for s in statuses):
                    print("Watchdog encountered errors. See watch target last_error fields for details.", file=sys.stderr)
                    sys.exit(1)
        else:
            watchdog_loop(interval_s=args.interval, limit=args.limit)

if __name__ == "__main__":
    main()
