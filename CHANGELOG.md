# Changelog

All notable user-facing changes are recorded here. AutoCedar follows semantic
versioning while the public provider and CLI interfaces stabilize.

## 0.2.0 - 2026-07-14

- Added provider-neutral model backends for Codex login, Claude Code
  (`claude -p`), Anthropic API keys, OpenAI API keys, and local
  OpenAI-compatible servers.
- Added provider-scoped model, effort, endpoint, and authentication controls
  to the interactive TUI.
- Split non-secret settings from API-key storage with private, atomic files and
  one-time migration from the legacy user `.env`.
- Isolated Stevens/Jarvis Slurm material under `autocedar-jarvis/`.
- Added pull-request CI for Python 3.11 and 3.12 and locked release installs.
- Removed the legacy Anthropic-shaped interface from provider-neutral runtime
  code.

### Migration note

The provider ID `openai` now means the direct OpenAI API. Codex OAuth uses the
provider ID `codex`; local vLLM and similar endpoints use `local`.

## 0.1.29 - 2026-07-14

- Hardened user configuration permissions and environment precedence.
- Kept automated review modes explicitly separate from human semantic
  approval.
- Corrected auto-approve completion status and duplicate-review bookkeeping.
