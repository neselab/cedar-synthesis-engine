# HITL Production Agent — Step C Plan

> Slim plan locking the Step C implementation contract. Most
> architectural decisions are inherited from
> ``HITL_STEP_B_PLAN.md``; this document pins only what's new for
> Step C (Stage 1 with real LLM integration + interactive terminal
> review loop).

---

## 1. Scope

Step C implements **Stage 1 with real LLM**:

- ``autocedar/llm.py`` — thin Anthropic SDK wrapper with a
  dependency-injection seam for mocking in tests. Supports prompt
  caching so the schema-atomization system prompt (large, stable) is
  cached across atom-proposal calls.
- ``autocedar/schema_atomizer.py`` — extends Step B's
  ``compose_schema`` with:
  - ``propose_schema_atoms(spec_text, llm)`` — LLM call returning a
    structured list of Stage 1 atoms, validated against the atom
    JSON shape from ``autocedar.atoms``.
  - ``compose_and_validate(draft, schema_path, llm)`` — compose →
    ``cedar validate`` → on failure, ask LLM to fix → re-validate.
    Bounded retries (max 3) per ``HITL_STEP_B_PLAN.md`` §6.4.
- ``autocedar/prompts/schema_atomization.md`` — the prompt template.
- ``autocedar/ui/terminal.py`` — interactive review loop with
  dependency-injected I/O for testability. Implements the
  ``[A]pprove / [R]eject / [E]dit / [Q]uestion / [S]ee Cedar /
  [V]iew patches`` keys from ``HITL_STEP_B_PLAN.md`` §6.2.

Out of scope (Step D and beyond):

- LLM-driven property atom proposal (Stage 2 LLM call). The Step C
  pipeline keeps Step B's stubbed Stage 2 proposer.
- Real synthesis loop (Stage 3 hooked into ``eval_harness``).

---

## 2. Locked decisions

### 2.1 Model choices

Current implementation note: this plan predates the Codex-provider pivot.
AutoCedar now defaults all live model-backed steps to Codex OAuth with
`gpt-5.5`; Anthropic is an explicit opt-in provider only.

Default model: **`claude-opus-4-7`** per the `claude-api` skill's
non-negotiable default ("never downgrade for cost — that's the user's
decision, not ours"). The schema-atomization task is a multi-step
reasoning task with structured output: Opus's adaptive thinking and
the effort parameter are load-bearing for getting it right on the
first try.

| Stage | Model | Notes |
|-------|-------|-------|
| Schema atomization (`propose_schema_atoms`) | `claude-opus-4-7` | Adaptive thinking + `effort: "high"`. |
| Schema-fix on validate failure | `claude-opus-4-7` | Same model retries with the validator's error text appended. |
| LLM-driven alternative proposer in grounding.py (deferred to Step D) | `claude-opus-4-7` | Same complexity tier; can downgrade per-deployment. |

Model identifier is configurable via constructor argument so
deployments that prefer Sonnet 4.6 (cost) or want to pin a specific
model can override. The default lives in `autocedar/llm.py` as a
module constant so tests pin a known model name.

### 2.2 Output format

LLM returns a **JSON array of atom records** wrapped in a code
fence. The proposer prompt explicitly asks for fenced JSON; the
parser tolerates either fenced or bare JSON (similar to the
``_extract_json_block`` helper already in ``autocedar.critic``).

Each atom record has a ``kind`` field discriminating entity /
attribute / action / type_alias, plus the AtomBase fields and
kind-specific fields. The parser routes by ``kind`` into the right
dataclass via ``autocedar.atoms.from_dict``.

Tool use (the Anthropic SDK's structured output mode) is a future
option but adds boilerplate; the JSON-via-prompt approach is simpler
for Step C and battle-tested in the existing harness.

### 2.3 Prompt caching

The system prompt and the spec text are stable across multiple
LLM calls in one session (proposal, edits, fix-attempts). Mark these
as cache-controlled per the Anthropic prompt-caching docs to amortize
input-token cost across the session.

Concretely: the system prompt and the spec are sent as a single
cache-breakpoint block; per-turn user content (the request itself)
follows uncached.

### 2.4 Mocking strategy

The LLM client is a class with a ``call_messages`` method. Tests
inject a mock client whose ``call_messages`` returns scripted
responses, exercising the proposer/fixer/review code paths without
network I/O.

Real LLM tests are kept separate (marked ``@pytest.mark.live``) and
default-skipped; they run only when ``ANTHROPIC_API_KEY`` is set and
``--run-live`` is passed.

### 2.5 Interactive review loop testability

The review loop accepts ``input_fn: Callable[[str], str]`` and
``output_fn: Callable[[str], None]`` as injected I/O so tests can
script user inputs without touching stdin/stdout. The default I/O
binds to ``input``/``print``.

The review loop returns a list of ``AtomDecision`` objects with both
``intent_acknowledged_by_user`` and ``symbolic_verified`` populated,
matching the Step B corpus contract.

---

## 3. Acceptance criteria

Step C is done when:

1. ``autocedar/llm.py`` has an ``LLMClient`` class. Construction
   defaults to the Anthropic SDK; tests inject mock clients. Prompt
   caching is enabled for the system+spec block.
2. ``autocedar/schema_atomizer.py`` has
   ``propose_schema_atoms(spec_text, llm)`` that calls the LLM,
   parses JSON, and returns a typed list of Stage 1 atoms. Round-
   trip through ``atoms.from_dict`` is unit-tested.
3. ``compose_and_validate(draft, schema_path, llm)`` runs
   ``cedar validate``; on failure, calls the LLM with the error text
   and the current schema; loops up to 3 attempts. Tests cover
   success on first try, success after one fix, and exhaustion.
4. The interactive review loop in ``autocedar/ui/terminal.py``
   handles all six keys (A/R/E/Q/S/V) and writes ``AtomDecision``
   records to the corpus with both verification flags. Tests use
   scripted ``input_fn`` to walk through each key.
5. End-to-end Stage 1 test: with a mocked LLM that returns a known
   schema, a scripted reviewer that approves all atoms, and an
   end-prose spec — Stage 1 produces a ``cedar validate``-passing
   schema and writes the full corpus shape.
6. Live test (gated): with a real Anthropic API key, the
   schema-atomizer proposes plausible atoms for a 1-paragraph spec
   and the resulting schema validates. Default-skipped.

---

## 4. Out of scope

- Stage 2 LLM-driven property atomization (Step D).
- ``eval_harness`` integration for Stage 3 synthesis (Step E).
- Web UI / TUI; terminal-only.
- Multi-spec batch mode.
- Anything that touches the v1 harness contract
  (``eval_harness.py`` / ``orchestrator.py`` / ``solver_wrapper.py``).

When the six acceptance criteria are met, Step C is signed off and
Step D (property elicitation with real LLM) starts.
