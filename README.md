# ResearchVault

**The local-first orchestration engine for OpenClaw.**

ResearchVault is a specialized "state manager" designed to help AI agents handle complex, multi-day investigations without losing their minds (or your tokens). 

### Why this exists:
Standard AI agents are great at answering questions, but they’re terrible at "staying the course" on a 5-hour research project. They forget what they’ve already searched, they repeat themselves, and they bloat your context window until it costs a fortune.

### Core Architecture:
* **The Vault:** A local SQLite ledger that tracks every query, every finding, and every sub-agent pulse. 100% private, 100% local.
* **Lifecycle Management:** Move projects from `active` to `completed` or `paused`. If your machine restarts, the research resumes exactly where it left off.
* **Cost Efficiency:** Built-in deduplication ensures you never pay for the same search query twice.

### Quick Start:
1. **Init:** `vault init --id "tech-audit" --objective "Deep dive into local LLM frameworks"`
2. **Log:** Agents record findings as they happen: `vault log --id "tech-audit" --type "FINDING" --payload '{"ollama": "v0.5 is faster"}'`
3. **Monitor:** See everything at once: `vault list`

---
*Built for OpenClaw. Developed by Edward. The alter-ego of Kalle.*
