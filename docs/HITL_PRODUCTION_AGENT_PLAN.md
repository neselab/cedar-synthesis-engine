# Cedar HITL Production Agent — Plan and Handoff

> Written 2026-05-07 for handoff to a new Claude instance. This document is
> self-contained: read it once and you have full context. Reference docs:
> `docs/harness_fix_log.md` (existing harness, §8.1–§8.11),
> `docs/lesson.md` (architectural overview), `cedarbench/README.md` (dataset),
> `CLAUDE.md` (quick orientation).

---

## TL;DR

We have a working two-phase CEGIS harness for Cedar policy synthesis (the
"v1 harness") that converges 121/121 of the original benchmark and 221
total scenarios. We've come to terms with the fact that **most scenarios
in our benchmark are transcription tasks**: the spec already names the
attributes, the schema is given, the verification plan and reference
bounds are pre-written. The harness's strong results on this benchmark
demonstrate that the policy-synthesis loop works **given good inputs to
it**, but the inputs themselves are the hard part of real Cedar authoring.

The plan is to **keep the existing benchmark and the v1 harness as a
Phase 0 baseline**, frame it honestly as such, and build a **Human-in-the-
Loop (HITL) production agent** that handles the full Cedar authoring
pipeline end-to-end — including schema design and property elicitation
— with the user validating each atomic decision.

The narrative arc for the paper becomes:

> Phase 0 (the v1 harness on the existing benchmark) shows that
> structured-feedback CEGIS converges with a small synthesizer model when
> given a schema, a verification plan, and reference bounds. Phase 1 (the
> HITL production agent) extends to real production input — natural-language
> specs of the kind a developer encounters — by atomizing schema design
> and property elicitation, validating each atom with the human, and
> handing the resulting verification plan to the v1 harness for the actual
> policy synthesis.

This document gives the new agent everything it needs to build Phase 1.

---

## 1. Context: where we are

### 1.1 What exists and works

- **`eval_harness.py` + `orchestrator.py` + `solver_wrapper.py`:** the v1
  harness. Two-phase architecture. Given a scenario directory containing
  `policy_spec.md`, `schema.cedarschema`, `verification_plan.py`, and
  `references/*.cedar`, it drives Haiku 4.5 to produce a Cedar policy that
  satisfies all properties via iterative CEGIS.
- **CedarBench (`cedarbench/scenarios/`):** 221 scenarios — 79 mutation
  scenarios auto-generated from cedar-examples, 142 hand-designed
  realworld scenarios across compliance, identity, payments, infrastructure.
- **Eleven signal-layer mechanisms** (§8.1–§8.11), each documented in
  `docs/harness_fix_log.md`. These are the technical novelty: directional
  feedback framing, hash oscillation detection, syntax-mismatch detectors,
  structural trap detectors.
- **Paper LaTeX project** at `/Users/zeitgeist/research/cedar-synthesis-paper/`
  (separate repo, builds 35-page PDF). Currently framed around the v1
  harness only. Will need restructuring per §6 of this document.

### 1.2 The pivot

We've discovered that the existing benchmark's specs are mostly
transcription targets. The spec literally names schema attributes by
name, embeds Cedar expressions in the prose, and warns the synthesizer
about specific traps. A real production input — a regulatory paragraph,
a Jira ticket, an internal HR memo — gives the agent none of these
hints.

The v1 harness is still useful: it solves the policy-synthesis sub-problem
once you have a schema and properties. But the part that's actually
hard in production is **getting to a schema and properties from prose**.
That part requires human judgment, and we believe the right architecture
is HITL: the agent proposes, the user validates, both sides converge on
a design.

---

## 2. Phase 0 baseline (the existing benchmark)

### 2.1 Reframing

The existing 221-scenario benchmark and v1 harness become **Phase 0**
in the larger story. The framing: "given a schema, a verification plan,
and reference bounds, can a small model produce a correct Cedar policy
via CEGIS with structured feedback?" Answer: yes, 121/121 PASS at $13.30
total cost. This is a useful baseline — it isolates the policy-synthesis
component and shows it works.

We do not pretend it solves end-to-end Cedar authoring. The new HITL
agent does.

### 2.2 Honest difficulty grading task

Before the new agent is built, **grade every existing scenario** for
synthesis difficulty. The grade reflects how hard it would be for a
small LLM to produce the policy given the inputs we currently provide
(spec + schema + properties + bounds).

**Rubric (1–5 scale):**

| Grade | Label                  | What it means |
|-------|------------------------|---------------|
| 1     | Trivial transcription  | Spec is a numbered list. Each bullet maps to one Cedar rule. Schema attributes named. No ambiguity. <10 lines of Cedar to write. |
| 2     | Easy transcription     | Larger transcription, possibly with one optional attribute or one set membership check. Still a one-pass task. |
| 3     | Moderate composition   | Multiple interacting rules where the synthesizer must compose conditions correctly. Some risk of getting bound wrong. |
| 4     | Genuinely hard         | A Cedar verifier quirk fights the synthesizer (§8.x territory). Or compound rule interactions where naive encoding fails. Without a known mechanism, model would stall. |
| 5     | Verifier-quirk hard    | Specifically requires §8.x-class harness intervention. Surfaced new mechanism when first run. |

**Procedure:**

1. For each scenario in `cedarbench/scenarios/` (mutation + realworld),
   read `policy_spec.md` only.
2. Estimate how many iterations a small LLM would take to produce a
   correct policy given (spec, schema, properties, bounds), assuming
   the v1 signal layer is enabled.
3. Assign a 1–5 grade based on the rubric.
4. Add a `synthesis_difficulty: <1-5>` field to the YAML frontmatter of
   `policy_spec.md`. For scenarios that already have a `difficulty:`
   field, add `synthesis_difficulty:` alongside (don't remove the
   original).
5. Save a manifest at `cedarbench/scenario_grades.json`:
   ```json
   {
     "github_add_contributor": {
       "synthesis_difficulty": 2,
       "rationale": "Bullet-list spec, 6 numbered roles each maps to one rule. No traps."
     },
     "tags_sensitivity_and_owner": {
       "synthesis_difficulty": 5,
       "rationale": "Required §8.11 ternary detector to converge. Nested record access with optional fields."
     },
     ...
   }
   ```
6. Produce a summary table in `cedarbench/SCENARIO_DIFFICULTY_SUMMARY.md`:

   ```
   | Grade | Count | % of total |
   |-------|------:|-----------:|
   | 1     | XX    | XX%        |
   | 2     | XX    | XX%        |
   | 3     | XX    | XX%        |
   | 4     | XX    | XX%        |
   | 5     | 5–7   | 2–3%       |
   ```

7. Commit with message
   `docs: grade all 221 scenarios on synthesis difficulty (1–5 honest scale)`.

**Expected outcome:** approximately 60% Grade 1–2, 30% Grade 3, 8%
Grade 4, 2–3% Grade 5. This is the honest baseline that frames the
paper.

**Effort:** ~4–6 hours of focused review.

---

## 3. The HITL production agent: vision

### 3.1 What it does

The agent takes a real input — an unstructured prose specification of
an access-control requirement (a regulatory excerpt, a product memo, an
HR document, a security review summary) — and walks the user through
producing a complete, verified Cedar policy.

The agent does **not** dump a fully-formed schema or policy on the user.
It atomizes each design decision, presents atoms one at a time (or in
small reviewable batches), gets user validation per atom, and only
commits to a design once the user has signed off.

### 3.2 Three stages

```
Stage 1 — Schema atomization (HITL)
  Input:  prose spec
  Output: validated Cedar schema

Stage 2 — Property elicitation (HITL)
  Input:  prose spec + validated schema
  Output: validated verification plan + reference bounds
          (the user decides what "correct" means)

Stage 3 — Policy synthesis (automated, uses v1 harness)
  Input:  spec + schema + verification plan + reference bounds
  Output: validated Cedar policy
```

Stage 3 is the existing v1 harness running unmodified. Stages 1 and 2
are new HITL components.

### 3.3 Why HITL

Two reasons:

1. **The hard parts (schema design, "what is correct?") require human
   judgment.** No formal verifier can tell you if your schema correctly
   captures the regulatory intent. Only a domain expert can. We bake
   that fact into the architecture rather than pretend the model can
   do it alone.
2. **The atomization makes review tractable.** Reviewing a complete
   schema against a 5-page regulation is hard. Reviewing one entity at
   a time, with the agent's reasoning per entity, is easy. Atomization
   converts a daunting holistic review into a sequence of small,
   focused review tasks.

### 3.4 What success looks like

For a 5-page HIPAA §164 excerpt as input, the agent produces a complete
Cedar policy with the following steps:

- Stage 1: ~10–20 minutes of human attention. The agent proposes
  ~6–12 entity/attribute/action atoms; the user approves, edits, or
  rejects each. The user's total time is concentrated on judgment
  calls (e.g., "should `clearanceLevel` be a Long or an enum?").
- Stage 2: ~10–15 minutes. The agent proposes ~10–25 properties (a mix
  of ceilings, floors, liveness checks). The user signs off on each.
- Stage 3: ~1–3 minutes, fully automated. The v1 harness runs the
  CEGIS loop and produces a verified policy.

Total human time: ~30 minutes for a complex regulation. Total agent +
verifier wall time: ~5 minutes. Total cost: <$2 per policy.

By contrast, doing this same work by hand in production today takes
hours-to-days of expert engineer time. **That's the value
proposition.**

---

## 4. Architecture in detail

### 4.1 Stage 1: Schema atomization + HITL validation

**Recommended design (the "(b) with structured per-atom review" pattern):**

The agent proposes a **draft schema as a list of atoms**, all at once,
and the user reviews each atom with full context of the rest. This is
strictly better than pure per-atom interactive (option (a) in the user's
framing) because:

- The user sees structural relationships (this attribute is on this
  entity, used in this action) without having to remember them across
  rounds.
- It reduces round trips when many atoms are uncontroversial.
- It allows the user to spot **omissions** (atoms the agent didn't
  propose) by looking at the whole picture.
- It allows global revisions ("rename `Clinician` to `Provider` everywhere").

It's strictly better than pure batch (option (b) in the user's framing)
because the **per-atom granularity** means the user doesn't have to
rewrite a paragraph to flag a single attribute issue — they tag the
specific atom and the agent revises just that part.

**Atom types:**

- **Entity atom:** `entity Clinician = { ... }` with rationale for why
  this entity exists and what real-world thing it models.
- **Attribute atom:** one attribute on one entity, with type, rationale,
  and the prose excerpt it was extracted from (e.g., "section 4 of the
  spec mentions a clinician's hospital affiliation").
- **Action atom:** `action viewRecord appliesTo {...}` with allowed
  principal/resource types, context schema, and rationale.
- **Type alias atom:** Cedar `type X = ...` if applicable.
- **Schema invariant atom (informal):** a non-Cedar comment capturing a
  cross-attribute constraint the schema implies (e.g., "if isContractor
  is true, then assignedTeam should be empty").

**HITL interface (what the user sees per atom):**

```
[Atom 3 of 14]  ATTRIBUTE
  On entity:  Clinician
  Field:      hospital: Hospital

  Why I'm proposing this: Section 1 of the spec says "every clinician
  belongs to a hospital" and section 3 enforces "no cross-hospital
  access." The hospital affiliation is therefore needed both to model
  the clinician and to evaluate the cross-hospital forbid.

  Source excerpt: "The primary principal is `Clinician`; the primary
  resource is `Record`. Every Clinician, Patient, and Record is
  associated with a Hospital entity."

  Alternatives I considered:
    - hospital: String (entity name)
    - hospitalId: String
  Why I chose Hospital entity: the spec's section 1 explicitly says
  "associated with a Hospital entity," implying entity-level reference.

  Actions:
    [A]pprove   [R]eject (and explain)   [E]dit   [S]ee related atoms
    [Q]uestion: "did you mean...?"
```

The user can:
- **Approve** the atom as-is.
- **Reject** with a reason; the agent will propose an alternative.
- **Edit** the atom inline (rename, change type, etc.).
- **See related atoms** (e.g., "show me everywhere `hospital` is used").
- **Ask a clarifying question** ("did you mean a single hospital
  association, or a list?"). The agent answers and may revise.

After each user action on an atom, the agent updates the draft. After
all atoms are processed, the agent shows the complete proposed schema
for one final holistic review. User signs off; the schema is written
to disk.

**Implementation sketch (Python pseudocode):**

```python
class SchemaAtomizer:
    def __init__(self, llm, verifier):
        self.llm = llm
        self.verifier = verifier   # cedar validate
    
    def propose_schema(self, spec_text: str) -> list[Atom]:
        """Produce initial draft as ordered list of atoms."""
        prompt = self._make_atomization_prompt(spec_text)
        atoms = self.llm.generate_structured(prompt, output_type=list[Atom])
        return self._reorder_for_review(atoms)
    
    def review_loop(self, atoms: list[Atom]) -> SchemaDraft:
        """User reviews each atom; agent revises in response."""
        decisions = []
        for atom in atoms:
            decision = self.ui.present_atom(atom)
            if decision.action == "reject":
                replacement = self.llm.propose_alternative(
                    atom, reason=decision.reason, context=decisions)
                atom = self.review_atom(replacement)  # recursive
            elif decision.action == "edit":
                atom = decision.edited_atom
            elif decision.action == "question":
                clarification = self.llm.answer(decision.question)
                self.ui.show(clarification)
                atom = self.review_atom(atom)  # re-present
            decisions.append((atom, decision))
        return self._compose(decisions)
    
    def synthesize_and_validate(self, draft: SchemaDraft) -> Path:
        """Compose atoms into a Cedar schema, validate it, return path."""
        schema_text = self._compose_schema_text(draft)
        result = self.verifier.validate_schema(schema_text)
        if not result.ok:
            # cedar validate caught a structural issue;
            # ask the LLM to fix and re-validate
            schema_text = self.llm.fix_schema(schema_text, result.error)
            result = self.verifier.validate_schema(schema_text)
        assert result.ok
        path = self._write(schema_text)
        return path
```

### 4.2 Stage 2: Property elicitation + user sign-off

Same atomization pattern as Stage 1, but the atoms are **properties**
rather than schema elements. The user is deciding what "correct" means
for the policy.

**Property atom types:**

- **Ceiling atom:** "X must not be permitted unless Y." Encoded as a
  reference policy that's an upper bound. Comes with the prose excerpt
  it was extracted from.
- **Floor atom:** "X must always be permitted when Y." Encoded as a
  reference policy that's a lower bound.
- **Liveness atom:** "X must be permitted for at least one input." (Often
  implicit; the agent generates one per action by default.)
- **Equivalence atom:** "X must be exactly equivalent to Y" (rare).
- **Disjointness atom:** "X must never permit anything Y permits" (rare).

**HITL interface:**

```
[Property 5 of 18]  CEILING
  Action:     viewRecord
  Description: "Cross-hospital view is forbidden"

  Source excerpt: Section 1 says "Cross-hospital access is never
  permitted, and no override applies to this rule."

  Reference encoding:
    permit (
      principal is Clinician,
      action == Action::"viewRecord",
      resource is Record
    ) when {
      principal.hospital == resource.hospital
      // Additional permit conditions remain in other ceilings
    };

  Why I'm calling this a ceiling: this property says "candidate may not
  permit a viewRecord request when hospitals differ." A ceiling
  enforces "candidate ⊆ this reference."

  Actions: [A]pprove  [R]eject  [E]dit  [S]ee related  [Q]uestion
```

The user signs off on each property. After all properties are reviewed
and the agent has revised based on feedback, the verification plan is
written and the references go to disk.

**Critical:** because the user has signed off on every property, "correct"
is now defined by the user, not by the agent's interpretation of the
spec. Stage 3's success means "satisfies the properties the user
endorsed," which is closer to real-world correctness than any automated
verification can be.

### 4.3 Stage 3: Policy synthesis (the existing v1 harness)

Stage 3 is the existing `eval_harness.py` running unmodified. The
inputs are:

- `policy_spec.md` (original prose, used by the LLM as context only)
- `schema.cedarschema` (produced by Stage 1)
- `verification_plan.py` (produced by Stage 2)
- `references/*.cedar` (produced by Stage 2)

The harness drives Haiku 4.5 to produce `candidate.cedar` via the v1
CEGIS loop with all 11 signal-layer mechanisms enabled.

**Crucially:** Stage 3 doesn't need any HITL because the user has
already validated everything that requires judgment. The agent and
verifier can solve this part in seconds with no human in the loop.

### 4.4 The full pipeline as a single command

```bash
autocedar author --input policy_spec.md --output ./my-policy/
```

Or interactively:

```bash
autocedar author --interactive
> Paste your specification (Ctrl-D to end):
> ...prose spec...
> ^D
[Stage 1: Schema atomization. Reviewing 14 atoms.]
[Atom 1 of 14] ENTITY: Clinician ...
> Approve: y
...
[Stage 1 complete. Schema validated. 14 atoms, 12 approved as-is, 2 edited.]
[Stage 2: Property elicitation. Reviewing 18 properties.]
...
[Stage 2 complete. Plan validated.]
[Stage 3: Policy synthesis. Running CEGIS loop...]
[Stage 3 complete. Policy converged in 4 iterations.]
[Output: my-policy/candidate.cedar]
```

---

## 5. Implementation roadmap

### Step A — Honest grading of v1 benchmark (~4–6 hours)

Per §2.2 above. Produces `cedarbench/scenario_grades.json` and
`cedarbench/SCENARIO_DIFFICULTY_SUMMARY.md`. Commits with descriptive
message. **Do this first.** It establishes the honest baseline before
any new agent work.

### Step B — Atom data model (~2–3 hours)

Define the Python dataclasses and JSON schemas for atoms:

```python
@dataclass
class EntityAtom:
    name: str
    members_of: list[str] = field(default_factory=list)  # parent entities
    attributes: dict[str, AttributeAtom] = field(default_factory=dict)
    enum_values: Optional[list[str]] = None
    rationale: str = ""
    source_excerpt: str = ""

@dataclass
class AttributeAtom:
    name: str
    type: str  # "Long", "String", "Bool", "datetime", "Set<X>", "Record{...}"
    optional: bool = False
    rationale: str = ""
    source_excerpt: str = ""
    alternatives_considered: list[str] = field(default_factory=list)

@dataclass
class ActionAtom:
    name: str
    principal_types: list[str]
    resource_types: list[str]
    context_attributes: dict[str, AttributeAtom]
    parent_groups: list[str] = field(default_factory=list)
    rationale: str = ""
    source_excerpt: str = ""

@dataclass
class PropertyAtom:
    name: str
    constraint_type: Literal["implies", "floor", "always-denies-liveness", ...]
    action: str
    principal_type: str
    resource_type: str
    reference_cedar: str  # the reference policy text
    rationale: str
    source_excerpt: str
```

Place: `autocedar/atoms.py` (new package alongside the existing harness
modules).

### Step C — Schema atomizer (Stage 1) (~1–2 weeks)

Build `autocedar/schema_atomizer.py` with:

- `SchemaAtomizer.propose_schema(spec_text)` — calls LLM with a
  structured prompt asking for an atomized draft. Output validated
  against the atom JSON schema.
- `SchemaAtomizer.review_loop(atoms)` — interactive review using a
  terminal UI. Per-atom present, accept user input, dispatch to LLM
  for alternatives or clarifications.
- `SchemaAtomizer.compose(decisions)` — turn the validated atoms into
  a `schema.cedarschema` text. Validate with `cedar validate`. If
  validation fails, ask the LLM to fix and revalidate.

**LLM prompt design** for `propose_schema`:

> You are designing a Cedar schema from the following specification.
> Read it carefully and produce an atomized draft schema. For each
> atom, include: (a) what it is (entity, attribute, action), (b) why
> you're proposing it, citing specific spec text, (c) alternatives you
> considered and why you rejected them. Output as a JSON list of atoms.
> Do not produce the final schema text — just the atom list.
>
> [spec text follows]

The structured-output capability of modern LLMs (JSON mode, tool use)
makes this tractable.

**Terminal UI:** for the v1 of the agent, use a simple text-based UI.
For each atom, print the atom block, prompt for action (`a/r/e/s/q`),
handle accordingly. Persist state across sessions in a draft file
(JSON) so the user can pause and resume.

For a v2, consider a web UI or TUI (Textual library) for richer
interaction. Out of scope for the initial paper.

### Step D — Property atomizer (Stage 2) (~1–2 weeks)

Same shape as Step C but for properties. The LLM is prompted to:

> Given the spec and the validated schema, propose a verification plan
> as a list of property atoms. Each atom should have a constraint type
> (ceiling/floor/liveness/equivalence), the action it applies to, the
> reference policy text, and rationale tied to a specific spec excerpt.

Each proposed property is validated by:
- `cedar validate` on the reference policy (catches type errors).
- Joint satisfiability check: for each new floor atom, run
  `cedar symcc implies` against every existing ceiling atom to confirm
  the bounds are jointly satisfiable. If not, flag for user
  attention before sign-off (don't silently produce inconsistent bounds).

This is essentially the planner phase of the v1 harness, but
restructured around HITL atomic review and using the existing §8.3 and
§8.8 mechanisms (reference self-validation, floor-bound consistency).

### Step E — Pipeline driver and CLI (~1 week)

Build `autocedar/cli.py`:

```python
def author(spec_path: str, output_dir: str, interactive: bool = True):
    spec_text = read(spec_path)
    
    # Stage 1
    atomizer = SchemaAtomizer(llm, verifier)
    atoms = atomizer.propose_schema(spec_text)
    schema_draft = atomizer.review_loop(atoms)  # HITL
    schema_path = atomizer.synthesize_and_validate(schema_draft)
    
    # Stage 2
    elicitor = PropertyElicitor(llm, verifier)
    prop_atoms = elicitor.propose_properties(spec_text, schema_path)
    plan = elicitor.review_loop(prop_atoms)  # HITL
    elicitor.write_plan(plan, output_dir)
    
    # Stage 3
    harness = V1Harness()
    candidate = harness.run(output_dir)
    
    print(f"Policy synthesized at {candidate}")
```

Plus argparse, logging, draft-state persistence (so an interrupted
session can be resumed).

### Step F — Evaluation: HITL benchmark (~2–3 weeks)

Build a small evaluation set of **real production-style inputs**:

- 5 anonymized real Cedar use cases (FAANG security blogs, AWS
  Verified Permissions case studies)
- 5 regulatory excerpts (HIPAA §164 paragraphs, GDPR articles, state
  privacy laws)
- 5 fabricated-but-realistic internal documents (HR memos, security
  reviews, product requirements)

For each input, three measurements:

1. **Time-to-policy:** wall-clock time from prose input to validated
   `candidate.cedar`, including human review.
2. **Atom-level acceptance rate:** what fraction of agent-proposed
   atoms (entity, attribute, action, property) are accepted by the
   user without modification. Higher is better up to a point;
   if 100%, the agent might be over-deferential.
3. **Final policy correctness:** the user manually reviews the final
   policy and rates it on a 1–5 scale. Optionally, a domain expert
   reviews and identifies bugs.

The story of the paper becomes:

> v1 harness solves the inner CEGIS loop given good inputs
> (Phase 0 baseline, 121/121 on CedarBench).
> HITL agent gets to "good inputs" via atomic user validation
> (the key contribution).
> End-to-end: prose → policy in ~30 minutes of human attention.

### Step G — Paper restructure (~1 week)

The Cedar paper at `/Users/zeitgeist/research/cedar-synthesis-paper/`
needs to be restructured per §6 of this document.

---

## 6. Paper restructure

The current Cedar paper draft is built around the v1 harness only.
The new structure adds the HITL agent as the headline contribution,
with the v1 harness becoming the Phase 0 baseline.

**New title (proposed):**
"Human-in-the-Loop Cedar Policy Authoring: Atomized Schema Design and
Property Elicitation, Backed by Counterexample-Guided Synthesis"

**Section structure:**

1. **Introduction.** Cedar policy authoring is hard; LLMs alone
   transcribe specs but don't produce real production policies.
2. **Related work.** Same as current draft, plus citations on HITL
   AI design, mixed-initiative interfaces, and prompt-decomposition
   work.
3. **Phase 0: structured-feedback CEGIS for policy synthesis (the
   existing v1 harness contribution).** Compresses current
   `mechanisms.tex` into one section. Headline result: 121/121 PASS
   on the structured-input benchmark, demonstrating that the inner
   loop works.
4. **Phase 0 evaluation: CedarBench v1 with honest difficulty
   grading.** Reports the difficulty distribution from §2.2 honestly.
   Shows that the v1 harness handles all difficulty tiers including
   the few Grade-5 verifier-quirk scenarios.
5. **The atomization gap.** The honest framing: real Cedar authoring
   starts from prose, not from a structured spec. The v1 harness
   solves the inner loop but punts on the outer loop.
6. **Phase 1: HITL production agent.** The new contribution. Three
   stages (schema, properties, synthesis), atom-based HITL design,
   why atomization helps.
7. **Phase 1 evaluation: production-style inputs.** Time-to-policy,
   atom acceptance rate, correctness scoring on the small evaluation
   set from Step F.
8. **Discussion, limitations, future work.** As current draft.
9. **Conclusion.**

The current 11-mechanism appendix carries over to Phase 0's section.
A new appendix documents the HITL UX in detail.

---

## 7. Repository layout (target state)

```
cedar-synthesis-engine/
├── eval_harness.py                  # v1 harness (UNCHANGED)
├── orchestrator.py                  # v1 harness
├── solver_wrapper.py                # v1 harness
├── autocedar/                     # NEW HITL production agent
│   ├── __init__.py
│   ├── atoms.py                     # atom data classes
│   ├── schema_atomizer.py           # Stage 1
│   ├── property_elicitor.py         # Stage 2
│   ├── pipeline.py                  # orchestrates Stages 1–3
│   ├── cli.py                       # entry point
│   ├── ui/
│   │   ├── terminal.py              # text-based atom review UI
│   │   └── persistence.py           # save/resume draft state
│   └── prompts/
│       ├── schema_atomization.md    # prompt template for Stage 1
│       └── property_elicitation.md  # prompt template for Stage 2
├── cedarbench/                      # v1 benchmark (UNCHANGED)
│   └── scenarios/
├── cedarbench_hitl/                 # NEW: real production inputs
│   ├── README.md
│   └── scenarios/
│       ├── hipaa_164_view_amend/
│       │   ├── input.md             # the prose spec ONLY
│       │   ├── reference_schema.cedarschema    # ground-truth schema
│       │   ├── reference_plan.py    # ground-truth plan
│       │   └── reference_policy.cedar          # ground-truth policy
│       └── ...
├── docs/
│   ├── HITL_PRODUCTION_AGENT_PLAN.md   # this document
│   ├── harness_fix_log.md           # v1 mechanisms (UNCHANGED)
│   ├── lesson.md                    # v1 architecture (UNCHANGED)
│   └── hitl_ux.md                   # new: HITL UX details
└── CLAUDE.md                        # update with HITL pointer
```

---

## 8. Open design questions for the user

**Q1: Schema atomization style.**
We recommend (b)-with-per-atom-review — agent proposes a complete
draft, user reviews each atom but sees the whole context. Confirm or
push back.

**Q2: Property atomization scope.**
Should the agent propose **only** ceilings/floors/liveness, or should
it also propose richer property types like equivalence, disjointness,
or quantitative properties (rate limits, cardinality bounds)? The v1
harness only knows ceiling/floor/liveness; expanding requires harness
work too.

**Q3: User skill level assumption.**
Is the target user (a) a Cedar expert who can read reference policies,
or (b) a non-Cedar developer who needs the agent to translate Cedar
back to prose for review? For (b), each atom needs a "Cedar-free"
explanation in addition to the technical content. We recommend (a) for
the initial paper, with (b) as future work — but worth confirming.

**Q4: Stage 1.5 — schema iteration based on Stage 2 feedback.**
Sometimes the user, while reviewing properties in Stage 2, realizes
the schema doesn't capture some attribute. Should we allow Stage 2 to
go back and revise the schema (Stage 1.5), or freeze the schema once
Stage 1 ends? We recommend allow-back-to-1.5 with explicit user
trigger; freezing is too rigid for real authoring.

**Q5: Cost / latency budget.**
What's the acceptable per-policy cost and latency? Our current v1
harness costs ~$0.10 per policy at small-model scale. The HITL agent
will add 2–4 LLM calls per Stage-1 atom proposed/revised plus some
calls in Stage 2. Estimated additional cost: $1–$5 per policy. Latency
will be dominated by user review time (~30 min) so per-call latency
of a few seconds is fine.

**Q6: Persistence and audit trail.**
The HITL agent should produce a complete audit trail (every atom, every
user decision, every LLM proposal/response) for compliance and
reproducibility. Recommend storing as a structured JSON log per
session. Confirm.

---

## 9. Suggested first commit

The new instance should start with:

1. Read this entire document.
2. Read `docs/lesson.md` for v1 architecture.
3. Skim `docs/harness_fix_log.md` so you understand what the v1
   harness's signal layer does.
4. **Do Step A first** (honest grading of the existing benchmark).
   This is the cleanest entry point, doesn't require any new
   architecture, and produces a useful artifact for the paper.
5. Once Step A is committed, message back with the results and a
   proposal for which question (Q1–Q6) to resolve first before
   starting Step B.

The user's preference is to move forward decisively rather than spend
more time on framing/rationalization. Concrete deliverables over
discussion.

---

## 10. References within this repo

- `eval_harness.py` — v1 harness entry point. `run_scenario()` is the
  function the new agent's Stage 3 will call.
- `orchestrator.py:run_verification()` — per-property verifier.
- `solver_wrapper.py:CEDAR_PATH` — pinned path to the Cedar binary.
  Currently `/private/tmp/cedar/target/release/cedar`. May need
  updating to `/Users/zeitgeist/.cargo/bin/cedar` per recent findings.
- `docs/harness_fix_log.md` — full §8.1–§8.11 documentation.
- `cedarbench/PROPOSED_HARD_SCENARIOS.md` — design doc for the v2
  scenarios. Mostly transcription tasks (per §2 above). Useful for
  understanding what we built; not the path forward.
- `CLAUDE.md` — current dataset state. Will need updating after Step A
  to reflect the difficulty grading.
