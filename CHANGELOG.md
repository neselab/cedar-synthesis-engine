# Changelog

All notable user-facing changes are recorded here. AutoCedar follows semantic
versioning while the public provider and CLI interfaces stabilize.

## Unreleased

- Added `--noisy` for documents in which some sentences may not be
  requirements, such as the output of a sentence classifier. The schema is
  built and reviewed once and then fixed; a map scope the schema does not
  declare leaves the map; a map the reviewer still rejects after
  `--max-map-rounds` is used if it passes the structure checks, with its open
  objections recorded; and a requirement that gets no approved atom is dropped
  instead of stopping the run. A dropped condition removes its slice, and a
  dropped restriction denies its scope, so a drop allows less, never more.
  Each drop and its reason goes to `stage2/dropped_requirements.json`. Without
  `--noisy` nothing changes.
  Before Stage 2, `--noisy` completes the schema once for the mapped
  requirements: the model names the entity attributes and action context
  fields they need, in batches of 30, and each reviewed field that Cedar
  validates is added (`stage1_5/schema_completion.json`). New entity types and
  actions are not added there. Without this step, a fixed schema that missed a
  field (a context flag, a student's courses) dropped a real requirement.
  If a call to revise the map fails, for example a long map that outlasts
  the request deadline, `--noisy` uses the last reviewed map.
  When an atom in Stage 2 fails Cedar validation on a field the schema lacks,
  `--noisy` asks for that requirement's fields once more and checks the atom
  again. A sentence whose every atom says `when { true }` and was rejected by
  model review as not a requirement leaves the map without removing its slice:
  writer and reviewer agree it adds no condition. A resumed `--noisy` session
  keeps a map that was used without approval.
- A condition packet for a requirement already solved in some of its scopes
  asks only for the open scopes and names the solved ones. Before, it listed
  every scope again, and models rewrote the solved scope and skipped the open
  one until the requirement was dropped.
- In `--noisy`, when a scope has a slice whose own conditions are all
  `when { true }` next to slices with conditions, the reviewer is asked
  whether it is a real unconditional permission ("HCPs can modify the office
  visit") or a sentence about the interface ("links are generated to download
  the paper"). Slices are ORed, so such a slice allows every request and makes
  the real conditions dead. A slice the reviewer does not keep is removed and
  reported; answers go to `stage2/unconditional_slices.json`. When the
  schema completion adds no field for an atom that used a missing one, the
  rejection now says the field will not come and asks for declared
  attributes, so the next attempt does not repeat the field.
- The permissions question now tells the model that a note about sentences
  that may not be requirements concerns extra sentences, not missing
  permissions. Before, the model answered no on the strength of that note
  alone, which left every scope without a ceiling. A resumed map whose scopes
  have no answer is asked the question again.
- The `match-broadness` failure now says to write `when { true }` when a
  requirement adds nothing beyond its scope, instead of only pointing at
  undeclared fields.
- `--max-proposals` sets the Stage 2 proposal budget (default 128, as before).
  `--noisy` raises it to 12 per requirement, so long documents are not cut off.
- A model answer that does not parse as the requested JSON is asked again, up
  to three times. Before, one malformed answer ended the run.
- A restriction on a scope that lists every way to allow it and has none
  ("the system will not update the legacy data") needs no atom: the scope's
  ceiling already denies every request. A repaired prior atom keeps the
  requirement it was written for.
- Added `autocedar mcp`, a dependency-free stdio MCP server that lets coding
  agents check setup, verify workspaces, and run human-in-the-loop authoring.
  The server pauses at every atom until the agent relays the user's decision.
  Paused or failed runs report their session directory for `resume_session`.
- Added an AutoCedar plugin for Claude Code and Codex (`plugins/autocedar`),
  with an `autocedar` skill, plus marketplaces for both agents at the repo root.
- Moved the model-backed authoring callbacks into one `author_hooks` builder
  shared by `author`, `resume`, and the MCP server.
- Added the intent map, a task graph after LEAP's AND-OR blueprint. The model
  maps the whole document into scopes (one principal type, action, and resource
  type), slices (ways to be allowed, AND of conditions), conditions (requirement
  sentences with edges to their slices), and rules for interpretation. The map
  passes structure checks and review before any atom is written. Each condition
  then gets one condition atom per scope, proposed from context drawn from the
  map's edges rather than the six nearest sentences. Floors and ceilings are
  calculated from the approved conditions, so a floor can no longer miss a
  condition. A requirement counts as done only when an approved atom grounds it
  in every scope; synthesis starts only when every node of the map is solved,
  and otherwise the run stops and names the blocking requirements. The map
  replaces the keyword rule for finding requirement sentences. Runs without a
  map builder (the Python API without `map_intent`) keep the previous Stage 2.
- When the document does not say whether it lists every way to allow an action,
  the map leaves that scope unmarked and AutoCedar asks one yes/no question
  after the map is approved: is the list of permissions complete? Yes gives
  those scopes a ceiling equal to their floors; no treats the listed
  permissions as examples. Under `--model-review` the model answers, recorded
  as the model's assumption. Before, the map guessed, and the same document
  could get anywhere from 2 to 14 of 14 scopes marked complete.
- `--review-provider` and `--review-model` let `--model-review` use a different
  model from the one that writes the atoms, so a reviewer does not share the
  writer's blind spots. Without them nothing changes. Each model decision
  records the reviewing model.
- The map review names its objections: move a condition, add a missing one,
  reclassify or drop a sentence, or unmark a scope, each with exact ids.
  AutoCedar applies these itself and reviews the corrected map again; only
  other objections go back to the mapper, quoted one by one. Before, any
  rejection sent the whole map back with a free-text reason, so one detail the
  mapper could not fix ended the run.
- The map text shown to reviewers no longer lists a scope restriction inside
  every slice as well as under the restrictions, which made correct maps look
  inconsistent and get rejected.
- A scope the map does not mark complete always goes to the yes/no question;
  the map can no longer mark a list "examples only" on its own.
- Schema construction works with the Claude CLI provider; the CLI rejected the
  `discriminator` keyword in the schema-atom format.
- Fixed the schema-support check misreading `entity E = { ... }` (valid Cedar)
  as an entity without attributes, which reported false schema gaps and
  stopped runs with a fixed schema. Declared hooks that name nothing are
  skipped.
- Fixed intermittent `error_max_turns` failures with the Claude CLI provider:
  structured calls now allow the CLI to ask the model to fix an answer that
  fails the schema (up to 5 turns), retry up to twice if the call still runs
  out of turns or the CLI cannot parse the model's tool call
  (`malformed_tool_use_exhausted`), and report the CLI's error kind.
- When the intent map needs an action that the schema does not declare, AutoCedar
  now adds it through the reviewed schema repair that Stage 2 uses, and checks
  the same map again. It shares Stage 2's repair budget, so a fixed schema
  (`--max-schema-gap-repairs 0`) is unchanged. While the schema can grow, the
  mapper is told it may name new actions. When the schema review refuses an
  action, its scopes leave the map, and the map reviewer is told which
  sentences left and why, so the two reviews do not overrule each other in
  turn: map-review objections that ask again for those sentences are settled,
  and a rejection with only such objections approves the rest of the map.
  Before, the map could not name a requirement the generated schema had
  missed, so its review kept rejecting it until the run stopped.
- `--max-map-rounds` (default 3, as before) sets how many times the intent map
  can go back to the mapper. Long or noisy documents can need more rounds.
- Schema repair patches the schema as it stands, and falls back to recomposing
  the draft only when the text cannot be patched; a recomposed schema that drops
  a declared type or action is rejected. Patching now adds the comma a list needs
  and finds slots written on one line or without a trailing comma. A support gap
  still missing after its repair is not repaired again. Before, a schema whose
  types came from the validation fixer lost them on every repair, and one
  attribute was requested 67 times without end.
- When the schema review refuses a Stage 2 schema repair on the map path, the
  run goes on: that requirement's atoms are rewritten within the schema, with
  the review's reason in the instruction, and a requirement that still cannot
  be expressed stops the run by name. Before, one refused repair ended the run.
- Schema repair after a `cedar validate` failure has its own prompt. It used the
  schema-construction prompt, so a model could return schema atoms instead of
  the corrected schema, and the run ended on a parse error.
- A condition atom written as `when { true }` passes its checks again: it
  says the sentence only grants its scope ("Reviewers can view the overview"),
  and model or human review judges that reading. Any other condition that
  holds for every request of its scope still fails, as it usually means a
  `has` test on an undeclared field. Before, every sentence that only grants
  access was blocked, so runs on such documents stopped before synthesis.
- A condition whose arithmetic can overflow on its own (`+`, `-`, `*`, or
  datetime `.offset(...)`) is accepted when earlier requirements of its slice
  bound the operands; floors place it after them, so Cedar's `&&` checks the
  bounds first. The condition prompt now says so. Before, it told the model
  that AutoCedar rejects any condition that can raise an error, so models
  avoided `*` and invented schema fields for a product such as usage × rate.
- The Codex provider now sends a request again, after pauses of 5 and 15
  seconds within the call's deadline, when the service answers with an
  overload or gateway error (429, 500, 502, 503, 504), or with a failed
  response that reports overload inside a 200 stream. Before, one such answer
  ended the run.
- Fixed a crash, and a false tool error from the never-errors check, on a
  condition with a long chain of `||` or `&&` (about 60 terms or more).
  Cedar's JSON reader stops at 128 levels of nesting, so neither step goes
  through JSON any more: floors and ceilings join the atoms' `when` and
  `unless` clauses as written, and the never-errors check cuts the candidate
  into policies at the semicolons that end them and checks each as Cedar text.
- Runs without a person now review meaning. `--model-review` has the model
  judge each atom against the full requirements (supported by the text, right
  action and types, Cedar matching its summary, floors that keep every
  condition) and sends rejections to the repair planner. Before, the flag
  approved any atom whose Cedar passed the symbolic checks, so atoms that
  misread a requirement entered the target. `--auto-approve` is the earlier
  name and still works. The checks-only approval mode is removed. Model review
  never counts as human approval.
- A short "Label:" line no longer replaces the Markdown section it sits in; it
  becomes a sub-heading under that section. Templates that repeat "Allow this
  action if…:" under each action's heading previously merged every action's
  requirements into one section, so atoms were proposed for the wrong action.
  Markdown heading levels are now tracked explicitly, so a document that
  starts at "##" keeps its sections as siblings.
- Property packets now list nodes from the focus node's own section before
  nodes from other sections that merely share words.
- A property atom with no action, principal type, or resource type (such as a
  catch-all "deny unlisted actions" atom) now fails its admission checks and
  goes to review and repair. Before, it raised `ValueError` and ended the whole
  authoring run. The property prompt now says Cedar is default-deny and asks
  for one atom per action.
- Compiled plans now include a `never-errors` check for every request
  environment, so synthesis rejects candidates that can raise a Cedar
  evaluation error, such as datetime overflow, and feeds back the
  counterexample. `cedar symcc never-errors` analyzes one policy at a time, so
  the check parses the candidate with Cedar and checks each rule, naming the
  rule that can error. Atom admission uses the same check, so a reference
  with several policies now gets a verdict instead of a tool error. The
  synthesis and property prompts now show guarded datetime arithmetic instead
  of unguarded `.offset(...)`, which can overflow.
- Fixed verification of property atoms over several principal or resource
  types: compiled plans now emit one ceiling or floor check per type pair
  instead of checking only the first, which left the other types unbounded.
- Fixed Stage 1.75 and admission floor/ceiling checks to compare each pair in
  the request environments both atoms apply to. Previously every pair on an
  action was checked in the first floor's environment, which could miss real
  conflicts or report false ones.
- Stage 1.75 now also stops before synthesis when a ceiling or disjointness
  bound shuts out a liveness slice entirely, instead of leaving the run to fail
  at its iteration budget.
- Source nodes now join hard-wrapped lines and keep list markers with their
  item, so a wrapped requirement is one node rather than several fragments.
  Section numbers such as "§8.8" are no longer split as sentences. Node ids
  change for documents with wrapped lines, so resume a session only with the
  version that started it.

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
