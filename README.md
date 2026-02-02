# ResearchVault 🦞

**The local-first orchestration engine for high-velocity AI research.**

ResearchVault is a specialized state manager and orchestration framework for OpenClaw agents. It allows agents to handle complex, multi-step investigations by persisting state, instrumentation, and insights into a local SQLite "Vault."

Following the **Inference-Speed Development** philosophy, Vault is built CLI-first to close the loop between research planning and autonomous execution.

## ✨ Core Features

*   **The Vault (SQLite)**: A persistent, local ledger for queries, events, and findings. 100% private.
*   **Instrumentation 2.0**: Every research event tracks **Confidence** (0.0-1.0), **Source** (identifying specific agents/components), and **Tags** for granular filtering.
*   **Multi-Source Scuttling**: Specialized support for pulling signal from **X (Twitter)**, **Reddit**, and **Moltbook**.
*   **Suspicion Protocol**: Built-in logic to trust-weight data. Moltbook scans are automatically flagged as low-confidence (`0.55`) and tagged `#unverified` to filter out noise.
*   **Lifecycle & Priority**: Manage projects through `active`, `paused`, and `completed` states. Projects support **P{n} Priority Levels** for optimized focus.
*   **Semantic Cache**: Integrated deduplication to ensure you never pay for (or wait for) the same research query twice.
*   **Hardened Logic**: Comprehensive `pytest` suite ensuring 100% reliability of core database migrations and orchestration logic.

## 🚀 Workflows

### 1. Project Management
Initialize a project, set objectives, and assign priority levels.
```bash
python3 scripts/vault.py init --id "metal-v1" --name "Suomi Metal" --objective "Rising underground bands" --priority 5
```

### 2. Multi-Source Scuttling
Use the `scuttle` helper to automatically log findings with platform-aware confidence scores.
```bash
python3 scripts/scuttle.py --id "metal-v1" --source "Reddit" --query "Finnish death metal" --data "Ashen Tomb rising."
```

### 3. Verification & Testing
Run the integrated test suite via `uv` to verify system integrity.
```bash
uv run pytest
```

### 4. Monitoring
View sorted project lists and detailed event logs.
```bash
python3 scripts/vault.py list
python3 scripts/vault.py status --id "metal-v1"
```

## 🛠️ Development & Environment

ResearchVault is formalized using **uv** for dependency management and Python 3.13 stability.

*   **Core Architecture**: Modular design separating Interface (`vault.py`), Logic (`core.py`), and Storage (`db.py`).
*   **Oracle Loops**: Complex refactors use high-reasoning sub-agents.
*   **Main-Line Evolution**: Atomic improvements are committed directly to `main`.

---
*Built for OpenClaw. Developed by Edward (Alter-ego of Kalle, AI) and orchestrated by Luka Raivisto.*
