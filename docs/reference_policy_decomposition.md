# Reference Policy Decomposition: Ceilings & Floors

## The Core Problem

Generating a complete access control policy is **compositionally hard** for LLMs. A real-world policy is a conjunction of interacting rules: role checks, clearance gates, classification filters, department matching, forbid/permit ordering, and exception clauses. Every rule interacts with every other rule. LLMs struggle with getting this composition right — empirically as low as 36% accuracy on multi-rule policy synthesis.

## The Decomposition

Instead of asking an LLM to generate the full policy in one shot, we decompose the problem into two layers:

### 1. Reference Policies (Easy — one rule at a time)

Each reference policy encodes **one property** about **one action** as a single `permit` statement. No forbid/permit interaction, no ordering dependencies, no compositional complexity.

**Example:** The English rule *"Only Clinical Researchers with clearance above 3 can View non-HighlyRestricted docs in Active projects"* becomes:

```cedar
permit (principal, action == Action::"View", resource)
when {
    principal in Role::"ClinicalResearcher" &&
    principal.clearanceLevel > 3 &&
    resource.classification != "HighlyRestricted" &&
    resource.projectStatus == "Active"
};
```

This is a near-mechanical 1:1 translation from a single English sentence — well within LLM capabilities. Even weaker models handle this reliably.

### 2. Candidate Policy (Hard — composed by the agent)

The candidate policy is the full, multi-rule policy that must simultaneously satisfy all reference policies. This is the hard synthesis problem — and it's where the SMT solver feedback loop provides value.

## Two Types of Reference Policies

### Ceiling (Upper Bound) — "Never allow more than this"

The ceiling represents the **maximum permissive boundary** for an action. The candidate must never permit anything the ceiling wouldn't.

```
Verification:  implies(candidate, ceiling)
Meaning:       ∀ requests: candidate ALLOWS → ceiling ALLOWS
Catches:       Over-permissive bugs
```

**Example — `ceiling_view.cedar`:**
```cedar
// The MOST that should ever be allowed for View
permit (principal, action == Action::"View", resource)
when {
    resource.projectStatus == "Active" &&
    (principal.department == resource.projectManagingDepartment ||
     principal in Role::"GlobalAuditor") &&
    (
        (principal in Role::"ClinicalResearcher" &&
         principal.clearanceLevel > 3 &&
         resource.classification != "HighlyRestricted")
        ||
        (principal in Role::"PrincipalInvestigator" &&
         context.networkRiskScore < 20 &&
         context.isCompliantDevice)
    )
};
```

If the candidate uses `clearanceLevel >= 3` instead of `> 3`, the solver finds:
```
COUNTEREXAMPLE: clearanceLevel = 3 → candidate ALLOWS, ceiling DENIES
```

### Floor (Lower Bound) — "Must allow at least this"

The floor represents the **minimum required access**. The candidate must allow at least what the floor specifies.

```
Verification:  implies(floor, candidate)
Meaning:       ∀ requests: floor ALLOWS → candidate ALLOWS
Catches:       Over-restrictive bugs (e.g., a forbid rule that's too aggressive)
```

**Example — `floor_auditor_view.cedar`:**
```cedar
// A GlobalAuditor from a different department MUST be allowed View
permit (principal, action == Action::"View", resource)
when {
    principal in Role::"GlobalAuditor" &&
    principal in Role::"ClinicalResearcher" &&
    principal.clearanceLevel > 3 &&
    resource.classification != "HighlyRestricted" &&
    resource.projectStatus == "Active" &&
    principal.department != resource.projectManagingDepartment
};
```

If the candidate's `forbid` rule blocks cross-department access without exempting GlobalAuditors, the solver finds:
```
COUNTEREXAMPLE: GlobalAuditor + ClinicalResearcher, different departments
  → floor ALLOWS, candidate DENIES (forbid blocks them)
```

## The Correctness Envelope

A candidate policy is **correct** when it sits between the floor and ceiling:

```
     ┌─────────────────────┐
     │      CEILING         │  ← candidate never allows more than this
     │                     │
     │   ┌─────────────┐   │
     │   │  CANDIDATE   │   │  ← correct: floor ≤ candidate ≤ ceiling
     │   └─────────────┘   │
     │                     │
     │   ┌─────────────┐   │
     │   │    FLOOR     │   │  ← candidate always allows at least this
     │   └─────────────┘   │
     └─────────────────────┘
```

## Why This Works for Any Model

| Task | Difficulty | Who handles it |
|------|-----------|---------------|
| NL → single reference policy | **Easy** (1:1 translation) | LLM (even small models) |
| Reference policies → NL | **Easy** (summarization) | LLM (for admin review) |
| Full candidate synthesis | **Hard** (composition) | LLM + SMT feedback loop |
| Verifying candidate correctness | **Impossible for LLM** | SMT solver (CVC5) |

The formal guarantee comes from CVC5, not the LLM. The LLM just needs to be smart enough to read a counterexample and make a local fix — a much lower bar than full policy synthesis. Weaker models may take more iterations, but the loop still converges because each counterexample provides high-signal, actionable feedback.

## Structure Per Experiment

Each scenario needs **one ceiling per action** (because `cedar symcc implies` is scoped to a single action) and **one floor per property** you want to guarantee:

```
workspace/references/
├── ceiling_view.cedar          # Upper bound for View
├── ceiling_edit.cedar          # Upper bound for Edit
├── floor_auditor_view.cedar    # Lower bound: auditor loophole for View
└── floor_auditor_edit.cedar    # Lower bound: auditor loophole for Edit
```

Liveness checks (not-always-denies) don't need reference files — they operate directly on the candidate.

## Experiment Inputs & Outputs

### Inputs (per scenario)

| File | Who creates it | What it contains |
|------|---------------|------------------|
| `schema.cedarschema` | Human | Entity types, attributes, actions — the type system |
| `policy_spec.md` | Human | Natural language access control requirements |
| `verification_plan.py` | Agent A (or human) | List of checks: implies, floor, liveness |
| `references/*.cedar` | Agent A (or human) | Ceiling policies (upper bound) + floor policies (lower bound) |
| `policy_store.cedar` | Accumulated | Previously verified policies for this org/schema — the candidate must coexist with these |

### Minimum input

The **minimum** per experiment is just:
1. A `.cedarschema` (schema)
2. A `policy_spec.md` (NL requirements)

Agent A can generate the verification plan and reference policies from these two files. The admin reviews them via `review.py` before synthesis begins.

### Outputs

| Output | What it contains |
|--------|-----------------|
| `candidate.cedar` | The synthesized policy, written by Agent B through the feedback loop |
| Orchestrator output | Loss count, per-check pass/fail, and counterexamples for failures |
