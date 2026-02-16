# Changelog

## [3.0.2] - 2026-02-16

### Security
- Registry manifest transparency: surfaced `install` and full optional `env` map as top-level `SKILL.md` frontmatter fields to eliminate hidden install/env metadata mismatch.
- OpenClaw DB scope tightened by default: portal candidate discovery and DB selection under `~/.openclaw/workspace` now require explicit `RESEARCHVAULT_PORTAL_SCAN_OPENCLAW=1`.
- Secrets handling made explicit: portal-entered provider secrets are in-memory by default, persist only with `RESEARCHVAULT_PORTAL_PERSIST_SECRETS=1`, and inject into subprocess env only with `RESEARCHVAULT_PORTAL_INJECT_SECRETS=1`.
- Portal auth consistency: backend remains strict on `RESEARCHVAULT_PORTAL_TOKEN`; `start_portal.sh` now always initializes/exports the token from `.portal_auth` and avoids printing tokenized URLs unless explicitly requested.
- Added regression tests for OpenClaw scan gating, DB allowlist behavior, token strictness, and secret persistence/injection controls.

## [2.6.2] - 2026-02-10

### Security
- **SSRF Hardening**: Implemented strict DNS resolution and IP verification in `scuttle`. Blocks private, local, and link-local addresses by default.
- **Service Isolation**: Moved background services (MCP, Watchdog) to `scripts/services/` to reduce default capability surface.
- **Transparency**: Added `SECURITY.md` and updated `SKILL.md` manifest to explicitly declare optional environment variables.
- **Model Gating**: Explicitly set `disable-model-invocation: true` at the registry manifest level to prevent autonomous AI side-effects.

### Added
- `--allow-private-networks` flag for `vault scuttle` to allow fetching from local addresses when explicitly requested by user.
- Comprehensive provenance info: `LICENSE`, `CONTRIBUTING.md`, and project `homepage`.

### Fixed
- Registry metadata mismatch: standardized frontmatter keys for ClawHub compatibility.
- Removed `uv` requirement from primary installation path.
