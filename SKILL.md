---
name: vault
description: "Local orchestration framework for research."
tags:
  - factory-building
  - vibe-coding
  - inference-speed
  - cli-first
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

## Strategy: Inference-Speed Development

Following the "Shipping at Inference-Speed" philosophy:
- **CLI-First**: Everything starts as a CLI tool. Agents call it, verify it, and close the loop.
- **Factory Building**: Don't just build code; build systems that build code. Use `vault` to orchestrate multiple atomic updates.
- **Vibe Coding**: Trust the model to refactor and implement; spend your time on system design and framework choices.
- **Main-Line Evolution**: Commit atomic, working changes directly to `main`. Skip the overhead of complex branching for solo development.
- **Oracle Loops**: Use advanced reasoning models (like `gemini-3-pro-preview` or `o1`) as an "Oracle" when stuck on complex refactors.

## Maintenance

The vault database is excluded from version control to protect sensitive research data. Only the orchestration code is committed to GitHub.
