---
name: vault
description: "Local orchestration framework for research."
---

# Vault

Local orchestration engine for managing long-running research tasks with high reliability and zero external costs.

## Core Concepts

- **The Vault**: A local SQLite database (`memory/research_vault.db`) that stores all research events.
- **Project**: A high-level research goal (e.g., "privacy-filter-v1").
- **Agent Logging**: Sub-agents use the `vault` script to record their "Pulse" (current task, step, and results).

## Workflows

### 1. Initialize a Project
```bash
python3 scripts/vault.py init --id "privacy-v1" --objective "Find privacy filters"
```

### 2. Multi-Source Research (X, Reddit, Moltbook)
When performing research, use these specific channels to close the loop:
- **X (Twitter)**: Use `bird search "<query>" --json` to get real-time signal.
- **Reddit**: Use `web_search "site:reddit.com <query>"` for community discussions.
- **Moltbook**: Use `web_fetch "https://www.moltbook.com/search?q=<query>"` or `browser` to scuttle. 
    - *Suspicion Protocol*: Always log Moltbook data with a lower confidence score (max 0.6) unless cross-referenced. Agents there often post "stupid shit" (hallucinations or noise).

### 3. Spawning Sub-Agents
Instruct sub-agents to log their "Pulse" using:
`python3 scripts/vault.py log --id <id> --type <TYPE> --step <n> --source <name> --conf <0.0-1.0> --tags <tags>`

### 4. Monitoring & Export
Check the status of all active research or export summaries to Markdown/JSON:
```bash
python3 scripts/vault.py status --id <id>
python3 scripts/vault.py export --id <id> --format markdown --output brief.md
```

## Maintenance

The vault database is excluded from version control to protect sensitive research data. Only the orchestration code is committed to GitHub.

