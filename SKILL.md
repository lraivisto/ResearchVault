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
python3 skills/vault/scripts/vault.py init --id "privacy-v1" --objective "Find privacy filters"
```

### 2. Spawning Sub-Agents
When spawning a sub-agent, provide the project ID and instruct it to log progress:
"Log your progress using: `python3 bin/vault.py log --id <id> --type STEP_BEGIN --step <n>`"

### 3. Monitoring
Check the status of all active research:
```bash
python3 skills/vault/scripts/vault.py status --id <id>
```

## Maintenance

The vault database is excluded from version control to protect sensitive research data. Only the orchestration code is committed to GitHub.
