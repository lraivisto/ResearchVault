---
name: researchvault
description: "Local-first research orchestration engine. Manages persistent state, synthesis, and autonomous verification for agents."
metadata:
  {
    "openclaw":
      {
        "requires": { "python": ">=3.13" },
        "install":
          [
            {
              "id": "vault-venv",
              "kind": "exec",
              "command": "python3 -m venv .venv && . .venv/bin/activate && pip install -e .",
              "label": "Initialize ResearchVault (Standard)",
            },
          ],
        "disableModelInvocation": true,
      },
  }
---

# ResearchVault 🦞

Autonomous state manager for agentic research.

## Security & Privacy (Local First)

- **Local Storage**: All data is stored in a local SQLite database (~/.researchvault/research_vault.db). No cloud sync.
- **Network Transparency**: Outbound connections occur ONLY for user-requested URL ingestion (scuttle) or Brave Search API (if configured). No hidden telemetry or background crawling.
- **Explicit Invocation**: High-latency or network-active features (MCP server, Watchdog) must be explicitly started by the user.
- **No Model Auto-run**: disableModelInvocation: true ensures the model cannot autonomously start background processes.

## Installation

### Standard (Recommended)
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
```

### Fast Path (if you use uv)
```bash
uv venv && uv pip install -e .
```

## Quick Start

1. **Initialize Project**:
   ```bash
   python scripts/vault.py init --objective \"Track tech trends\" --name \"Tech-2026\"
   ```

2. **Ingest Data**:
   ```bash
   python scripts/vault.py scuttle \"https://example.com\" --id \"tech-2026\"
   ```

3. **Autonomous Strategist**:
   ```bash
   python scripts/vault.py strategy --id \"tech-2026\"
   ```

## Environment Variables

- RESEARCHVAULT_DB: Path to SQLite database.
- BRAVE_API_KEY: (Optional) Required for live search and verification missions.
