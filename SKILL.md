---
name: research-vault
description: "Local-first research vault for investigations: project ledger (SQLite), branch-aware findings/events, ingestion (web/Reddit/YouTube), synthesis links, verification missions, watchdog automation, and MCP access."
---

# ResearchVault

Local-first orchestration engine for managing long-running research tasks with a persistent SQLite vault. Some workflows optionally use external APIs (e.g. Brave Search) when configured.

## Core Concepts

- **The Vault**: A local SQLite database stored at `~/.researchvault/research_vault.db` (configurable via `RESEARCHVAULT_DB`).
- **Project**: A high-level research goal.
- **Branch**: A divergent reasoning line inside a project (default: `main`).
- **Hypothesis**: A trackable claim/rationale attached to a branch.
- **Instrumentation**: Every event tracks confidence (0.0-1.0), source, and tags.

## Configuration

- `RESEARCHVAULT_DB`: Override the SQLite path (default: `~/.researchvault/research_vault.db`).
- `BRAVE_API_KEY`: Enables live Brave search, verification mission execution, and query watch targets. Without it, you can still run offline-ish flows (manual findings, URL scuttle, synthesis), and you can inject cached search results via `python -m scripts.vault search --set-result`.

## Workflows

### 1. Initialize a Project
```bash
uv run python -m scripts.vault init --id "proj-v1" --objective "Project goal"
```

### 2. Divergent Reasoning (Branches + Hypotheses)
```bash
uv run python -m scripts.vault branch create --id "proj-v1" --name "alt" --hypothesis "Competing explanation"
uv run python -m scripts.vault hypothesis add --id "proj-v1" --branch "alt" --statement "Key claim needs corroboration" --conf 0.55
```

### 3. Multi-Source Research (Scuttle)
Use the unified scuttle command (SSRF-protected) to ingest a URL into the Vault. Supported connectors include web pages, Reddit (via `.json`), and YouTube metadata. (Moltbook/Grokipedia connectors exist primarily as demos/examples.)
```bash
uv run python -m scripts.vault scuttle "https://example.com" --id "proj-v1" --branch "main"
```

### 4. Cross-Artifact Synthesis
Register local files as artifacts, then synthesize similarity links:
```bash
uv run python -m scripts.vault artifact add --id "proj-v1" --path "./notes.md" --type "NOTE"
uv run python -m scripts.vault synthesize --id "proj-v1" --threshold 0.78 --top-k 5
```

### 5. Active Verification Protocol
Generate and run verification missions for low-confidence / `unverified` findings:
```bash
uv run python -m scripts.vault verify plan --id "proj-v1" --threshold 0.7 --max 20
uv run python -m scripts.vault verify list --id "proj-v1" --status open
uv run python -m scripts.vault verify run --id "proj-v1" --limit 5
```

### 6. Watchdog Mode
Add watch targets and run one iteration:
```bash
uv run python -m scripts.vault watch add --id "proj-v1" --type url --target "https://example.com" --interval 3600 --tags "seed"
uv run python -m scripts.vault watch add --id "proj-v1" --type query --target "my topic query" --interval 21600
uv run python -m scripts.vault watchdog --once --limit 10
```

### 7. MCP Server
Expose the Vault over MCP (stdio transport by default):
```bash
uv run python -m scripts.vault mcp --transport stdio
```

### 8. Monitoring & Summary
```bash
uv run python -m scripts.vault summary --id "proj-v1"
uv run python -m scripts.vault status --id "proj-v1"
```

### 9. Export
```bash
uv run python -m scripts.vault export --id "proj-v1" --format markdown --output summary.md
```

## Maintenance

The database is local-first by default and should stay out of version control.
