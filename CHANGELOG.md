# Changelog

All notable user-facing changes are recorded here. AutoCedar follows semantic
versioning while the public provider and CLI interfaces stabilize.

## Unreleased

- Added verifier-grounded guidance for undefined Cedar variables and set
  iteration. Property proposals must expose missing relation hooks for schema
  review instead of inventing iterator variables or dropping the relation.

- Fixed valid unfenced Cedar being corrupted during response extraction; show
  the actual parser diagnostic and stop repeated failed-candidate loops with
  saved per-attempt evidence and bounded synthesis context.
- Reject verifier/tool failures before model repair and require explicit SymCC
  verdicts, preventing timeouts or witness text from falsely passing liveness.
  Reject unsupported/empty plans instead of silently skipping checks.

- Made schema/property review progress and queued proposals recoverable after
  interruptions, added TUI `/resume` and `/pause`, and prevented reuse of an
  existing session directory from overwriting saved work.
- Disabled speculative synthesis after every property approval; removed
  duplicated proposal context and added TUI model-call timing/token records.
- Enforced a deadline on trickling Codex streams and shared it across retries;
  show elapsed time and stream synthesis progress while it runs.
- Unified CLI/TUI property-repair routing and preserved approved ceilings,
  schema scopes, and verification status during resume. Fixed-target synthesis
  now rejects invalid reviewed references instead of rewriting them.
- Hardened generated-plan escaping and Cedar condition splicing, stopped
  repeated identical no-progress proposals, and skipped symbolic work after a
  failed Cedar type/parse check.

- Added a maintained Qwen3.6 FP8 setup path for Stevens Jarvis, including
  secure Hugging Face cache separation, a CPU model-preparation job, and real
  chat/JSON-schema model smoke checks.
- Made the Jarvis student configuration ready to copy with the documented
  `compute`/`gpu-l40s` defaults and added a no-allocation preflight that checks
  each user's live Slurm access, CUDA module, and model storage.
- Isolated Jarvis model-server jobs from ports already occupied on shared GPU
  nodes and made startup require the model name configured for the current job.

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
