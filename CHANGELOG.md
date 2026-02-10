# Changelog

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
