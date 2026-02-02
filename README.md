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

## 🚀 Workflows

### 1. Initialize a Project
Set your objective and priority level.
```bash
python3 scripts/vault.py init --id "metal-v1" --name "Suomi Metal" --objective "Rising underground bands" --priority 5
```

### 2. Instrumented Research
Log research steps with metadata.
```bash
python3 scripts/vault.py log --id "metal-v1" --type "FINDING" --step 1 --source "Kalle" --conf 0.9 --tags "reddit,band" --payload '{"band": "Ashen Tomb"}'
```

### 3. Multi-Source Scuttling
Use the `scuttle` helper to automatically apply source-specific confidence and tags.
```bash
python3 scripts/scuttle.py --id "metal-v1" --source "Moltbook" --query "death metal" --data "Agent halluncination about a ghost band."
```

### 4. Synthesize Insights
Promote raw findings to high-level project insights.
```bash
python3 scripts/vault.py insight --id "metal-v1" --add --title "Top Bands" --content "Ashen Tomb and Tormentor Tyrant lead the scene." --tags "summary"
```

### 5. Monitor Pulse
View the status of all active research, sorted by priority.
```bash
python3 scripts/vault.py list
python3 scripts/vault.py status --id "metal-v1" --filter-tag "reddit"
```

## 🛠️ Development Strategy

Vault follows the **Shipping at Inference-Speed** model:
*   **CLI-First**: Logic is exposed via robust CLI tools for agent loop-closing.
*   **Oracle Loops**: Complex refactors use high-reasoning "Oracle" agents.
*   **Main-Line Evolution**: Atomic improvements are committed directly to `main` to maintain high momentum.

---
*Built for OpenClaw. Developed by Edward (AI Operator).*
