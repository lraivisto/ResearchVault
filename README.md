# ResearchVault 🦞

**The local-first orchestration engine for high-velocity AI research.**

ResearchVault is a specialized state manager and orchestration framework for OpenClaw agents. It allows agents to handle complex, multi-step investigations by persisting state, instrumentation, and insights into a local SQLite "Vault."

Following the **Inference-Speed Development** philosophy, Vault is built CLI-first to close the loop between research planning and autonomous execution.

## ✨ Core Features

*   **The Vault (SQLite)**: A persistent, local ledger stored in `~/.researchvault/` (configurable via `RESEARCHVAULT_DB`). 100% private.
*   **Normalized Evidence Core**: Scalable storage for `artifacts`, `findings`, and `links` (graph-ready).
*   **Unified Ingestion Engine**: Modular connectors for automated research capture.
*   **Instrumentation 2.0**: Every research event tracks **Confidence** (0.0-1.0), **Source**, and **Tags**.
*   **Multi-Source Support**: 
    *   **X (Twitter)**: High-signal real-time data via `bird`.
    *   **Reddit**: Structured community discussions and top-comment trees.
    *   **Grokipedia**: Direct knowledge-base ingestion via API.
    *   **YouTube**: Metadata-only extraction (titles/descriptions) without API keys.
*   **Suspicion Protocol 2.0**: Hardened logic for low-trust sources. Moltbook scans are forced to low-confidence (`0.55`) and tagged `#unverified`.
*   **Semantic Cache**: Integrated deduplication for queries and artifacts.
*   **SSRF Safety**: Robust URL validation blocks internal network probes and private IP ranges.
*   **Hardened Logic**: Versioned database migrations and a comprehensive `pytest` suite.

## 🚀 Workflows

### 1. Project Management
Initialize a project, set objectives, and assign priority levels.
```bash
uv run python scripts/vault.py init --id "metal-v1" --name "Suomi Metal" --objective "Rising underground bands" --priority 5
```

### 2. Multi-Source Ingestion
Use the unified `scuttle` command to ingest data from any supported source (Reddit, YouTube, Grokipedia, Web).
```bash
uv run python scripts/vault.py scuttle "https://www.youtube.com/watch?v=..." --id "metal-v1"
```

### 3. Export & Reporting
Ship research summaries to Markdown or JSON for external use or agent review.
```bash
uv run python scripts/vault.py export --id "metal-v1" --format markdown --output summary.md
```

### 4. Verification & Testing
Run the integrated test suite to verify system integrity.
```bash
uv run pytest
```

### 5. Monitoring
View sorted project lists, high-level summaries, and detailed event logs.
```bash
uv run python scripts/vault.py list
uv run python scripts/vault.py summary --id "metal-v1"
uv run python scripts/vault.py status --id "metal-v1"
```

## 🛠️ Development & Environment

ResearchVault is formalized using **uv** for dependency management and Python 3.13 stability.

*   **Core Architecture**: Modular design separating Interface (`vault.py`), Logic (`core.py`), and Storage (`db.py`).
*   **Oracle Loops**: Complex refactors use high-reasoning sub-agents.
*   **Main-Line Evolution**: Atomic improvements are committed directly to `main`.

---
*This project is 100% developed by AI agents (OpenClaw / Google Antigravity / OpenAI Codex), carefully orchestrated and reviewed by **Luka Raivisto**.*
