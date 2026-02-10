# ResearchVault 🦞

**The local-first orchestration engine for high-velocity AI research.**

ResearchVault is a local-first state manager and orchestration framework for long-running investigations. It lets you persist projects, findings, evidence, instrumentation, and automation state into a local SQLite \"Vault\" so research can survive across sessions.

Vault is built CLI-first to close the loop between planning, ingestion, verification, and synthesis.

## 🛡️ Security & Privacy

ResearchVault is designed with a **Local-First, Privacy-First** posture:

*   **Local Persistence**: All research data stays on your machine in a local SQLite database (~/.researchvault/research_vault.db). No telemetry or auto-sync.
*   **Network Transparency**: Outbound connections are limited to:
    1.  User-requested scuttling (URL fetching).
    2.  Brave Search API (if a key is explicitly provided).
*   **Zero Auto-Start**: No background processes or long-running servers start during installation. The Watchdog and MCP server must be explicitly invoked by the user.
*   **Restricted Model Invocation**: The disableModelInvocation flag prevents the AI from autonomously triggering side-effects without a direct user prompt.
*   **SSRF Protection**: Built-in URL validation blocks access to private IP ranges and internal network hosts.

## ⚙️ Configuration

*   RESEARCHVAULT_DB: Override the SQLite path (default: ~/.researchvault/research_vault.db).
*   BRAVE_API_KEY: Enables live Brave search and verification missions.

## 🚀 Installation

### Standard (Standard Python)
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
```

### High Performance (using uv)
If you have [uv](https://github.com/astral-sh/uv) installed:
```bash
uv venv && uv pip install -e .
```

## 🛠️ Key Workflows

### 1. Project Management
Initialize a project and set research objectives.
```bash
python scripts/vault.py init --id \"ai-safety\" --name \"AI Safety Research\" --objective \"Monitor 2026 safety trends\"
```

### 2. Multi-Source Ingestion
Ingest data from Web, Reddit, or YouTube metadata.
```bash
python scripts/vault.py scuttle \"https://arxiv.org/abs/...\" --id \"ai-safety\"
```

### 3. Synthesis & Verification
Automate link-discovery and verify low-confidence findings.
```bash
python scripts/vault.py synthesize --id \"ai-safety\"
python scripts/vault.py verify run --id \"ai-safety\"
```

### 4. Autonomous Strategist (Next Best Action)
Get a recommended plan based on current project state.
```bash
python scripts/vault.py strategy --id \"ai-safety\"
```

## 📦 Dependencies

*   requests & beautifulsoup4: Targeted web ingestion.
*   rich: High-visibility CLI output.
*   mcp: Standard protocol for agent-tool communication.
*   pytest: Local integrity verification.

---
*This project is 100% developed by AI agents (OpenClaw / Google Antigravity / OpenAI Codex), carefully orchestrated and reviewed by **Luka Raivisto**.*
