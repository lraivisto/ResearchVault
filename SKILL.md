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

### 4. Monitoring
Check the status of all active research:
```bash
python3 scripts/vault.py status --id <id>
```

## Strategy: Inference-Speed Development

Following the "Shipping at Inference-Speed" philosophy:
- **Factory Building**: Don't just build code; build systems that build code. Use `vault` to orchestrate multiple atomic updates.
- **Oracle Loops**: Use `gemini-3-pro-preview` or `o1` as an "Oracle" via sub-agents for complex refactors.
- **Vibe Coding**: Trust the model to implement; focus on design.
- **CLI-First**: Everything starts as a CLI.
- **Ship to Main**: Commit atomic changes directly to `main`.

## Maintenance

The vault database is excluded from version control to protect sensitive research data. Only the orchestration code is committed to GitHub.
