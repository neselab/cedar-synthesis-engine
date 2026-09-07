# Authoring reliability and redundancy audit — 2026-09-07

The reported Retail session was running on Ubuntu. The supplied screenshot
shows property atomization at source 18/33, with 34 approved properties; it
does not identify the particular HTTP request or include its exception/logs.
The fixes below address code-confirmed failure paths. Recovery of that specific
session and its live token cost remain unverified until the updated code runs
against the saved Ubuntu session.

## Architectural contract

The [AutoCedar paper](https://arxiv.org/pdf/2607.03656), especially sections
III.A–C, separates reviewed target construction from candidate search. This
patch keeps that separation: human review owns intent; Cedar owns mechanical
checks; synthesis must satisfy the fixed reviewed target. Automated tests here
exercise recovery and control flow and do not stand in for semantic HITL review.

## Findings and changes

| Path | Finding | Change |
| --- | --- | --- |
| TUI → pipeline | `author this` never passed `resume_from`. Session artifacts were registered only on success. | Expose `/resume`; retain the session path before starting; find interrupted sessions for identical input; restore the last-session pointer on reopening. |
| Session storage | Same session IDs overwrote files; JSON writes could truncate on interruption; transcript events were memory-only until final flush. | Refuse occupied directories; generate collision-resistant IDs; write snapshots with temporary files, fsync, and atomic replacement; append audit events durably. |
| Stage 1 and Stage 2 | Accepted edits and unreviewed bundle members had no complete recovery snapshot. Decisions could be written after slow synthesis. | Checkpoint exact approved encodings, decisions, active source, and pending proposals. Save decisions before optional synthesis and save each schema-repair review before the next prompt. |
| Legacy resume | Source-citation overlap was treated as authority to delete older ceilings; action scopes were broadened and verification flags promoted during loading. | Restore the reviewed schema and properties without these semantic changes. Ordinary validation/admission remains responsible for reporting problems. |
| Authoring cost | The default pipeline synthesized a fresh candidate after every approved property. | Default to one final synthesis phase. Keep per-atom verification and final consistency checks. Explicit Python API opt-in retains experimental incremental synthesis. |
| TUI repair | The UI omitted the repair planner and fell back to a test implementation that always repaired the current property. | Share the same model-backed repair router across CLI author, CLI resume, and TUI. |
| Proposal context | Prior state appeared in source packets and prompts; approved atoms repeated source excerpts and empty metadata; repair prompts serialized full atom internals. | Keep approved Cedar encodings and compile-down fields, compact metadata, reference indexed sources by ID, omit redundant approval envelopes, and send prior state once. Keep substantive rejection/edit feedback. |
| Local provider | Output schema was supplied both as constrained response format and in conversational input. | Use the native schema once; add schema text only for prompt-only mode or unsupported-format fallback. |
| Codex transport | `readline()` could wait while bytes trickled in; per-read socket timeout did not enforce the intended elapsed-time limit. Each retry received a fresh budget. | Interrupt the response socket at the body deadline and share the generation deadline across retries. Keep the configurable 240-second default. |
| UI progress | Synthesis output was held until the whole run finished; a spinner had no elapsed time. | Forward complete output lines immediately, show elapsed time, and record structured-call usage and effective effort. |
| Property loop | Identical proposals could consume the global proposal budget without progress. | Stop after three identical proposals against unchanged source/schema/approved state, retaining checkpoints and an actionable failure. |
| Fixed-target synthesis | The harness could automatically rewrite broken approved references. | Authoring invokes fixed-target mode: missing/invalid targets fail for review instead of being silently regenerated. |
| Grounding and compilation | Symbolic checks repeated work after a failed parse/type gate. Multiline summaries broke generated Python; `when`/braces in strings/comments confused Cedar splicing. | Stop dependent checks after gate failure; escape generated literals; reject duplicate/path-traversing property names at compilation; ignore strings/comments when locating condition braces. |

## Redundancy measurement

An offline replay used the existing local saved fixture
`ibm-live-coverage-guard-20260629-resumed` (26 approved properties, 25 decision
records), comparing the pre-patch `LLMClient` at `92b83f8` to the new one. The
same first source neighborhood and placeholder schema string were supplied to
both; provider JSON-schema overhead was not included. Application prompt text
fell from **114,948 to 39,903 characters (65.3%)**. All 26 approved Cedar
encodings remained in the request. This isolates context duplication; it is
not a billed-token, live latency, or Retail measurement.

Separately, for a session with N property approvals and no additional repairs,
the old default scheduled N speculative synthesis runs plus final synthesis.
The new default schedules final synthesis only. Each synthesis run may itself
make multiple model calls, so this removes more than just duplicate prompt
text. It does not reduce the final verifier obligations.

## Validation and coverage

The audit traced the CLI/TUI entrypoints, source packets, schema/property
construction and repair, persistence, provider adapters, grounding, compile-down,
target admission, synthesis adapter, CEGIS feedback loop, and result reporting.
Existing provider/auth/configuration, corpus, dataset-tooling, translation, and
verifier regression suites were also run. This is not a claim that every
possible defect in the repository has been eliminated.

Local validation: **490 tests passed, 1 skipped**. Source and wheel distributions
built successfully; the packaged wheel includes the new persistence module.

Added regression coverage includes failure halfway through property/schema
bundles, schema-repair interruptions, changed-input rejection, session collisions,
atomic-replace failure, legacy ceiling preservation, completed-source recovery,
stagnation limits, TUI resume/save routing, token accounting, streamed synthesis
output, and a real socket that trickles an incomplete SSE line. A real Cedar
test confirms fixed-target rejection of an invalid reference without a model
repair call. No external model or scripted semantic reviewer is needed for
these tests.

## Remaining architecture work

- The pipeline remains a large imperative function. A durable state machine
  with explicit pending proposal/review/repair transitions should replace the
  separate state projections over time; current snapshots preserve backward
  compatibility without requiring that migration before recovery works.
- Every proposal still receives all approved formal encodings. This retains
  global/sibling constraint visibility but grows with the target. Replacing it
  with indexed retrieval needs explicit dependency closure and tests showing
  that omitted context cannot hide conflicting constraints. Text similarity
  alone is insufficient.
- Source-neighborhood selection and coverage heuristics warrant a dedicated
  completeness evaluation. An empty model bundle is not independent proof that
  the natural-language source has been captured faithfully.
- CLI and TUI still duplicate some callback wiring and configuration despite
  sharing repair routing. A single authoring runtime should own callbacks,
  telemetry, cancellation, and state transitions for both front ends.
- Pause is cooperative: it waits for an active model or verifier invocation.
  The stream-body deadline is covered by fault injection; arbitrary slow DNS,
  connection establishment, and malicious HTTP-header trickling are not a
  comprehensive transport cancellation guarantee.
- Legacy sessions can restore only evidence actually written by their version.
  New Stage 1 checkpoints cannot recover already-lost edits from an old run.
  The Ubuntu Retail session itself was not available for forensic replay.
