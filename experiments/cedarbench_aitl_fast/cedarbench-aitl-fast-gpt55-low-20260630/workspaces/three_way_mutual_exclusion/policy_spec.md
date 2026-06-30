---
pattern: three-way pairwise mutual exclusion (SoD across three actions)
difficulty: medium
features:
  - same-person-forbid across three pairwise action pairs on the same resource
  - optional context attributes for prior-actor attestation
  - has-guarded reads (canonical positive form)
domain: change management / SOX-style controls
synthesis_difficulty: 4
---

# Three-Way Mutual Exclusion — Policy Specification

## Context

This policy implements a strict three-way Separation of Duties for a
software-change-control workflow. A `ChangeRequest` is acted on by
three pairwise-mutually-exclusive roles in sequence: `submit`,
`approve`, and `audit`. The same `Engineer` must NEVER perform two of
these three actions for the same request.

The host application maintains the audit trail of which engineer
performed each prior action and attaches that information to the
incoming request as optional context attributes. When a prior action
has not yet been performed, the corresponding attribute is absent.

Principal is `Engineer`; resource is `ChangeRequest`. Three actions:
`submit`, `approve`, `audit`. Each action's context carries the
identities of the OTHER two actions' prior actors when they exist.

## Requirements

### 1. Submit (Not Prior Approver, Not Prior Auditor)
- An `Engineer` may `submit` a ChangeRequest provided they are NOT the
  engineer who previously approved this request AND NOT the engineer
  who previously audited it.
- Concretely: permit `submit` when:
  - `prevApprover` is absent OR `principal != context.prevApprover`, AND
  - `prevAuditor` is absent OR `principal != context.prevAuditor`.

### 2. Approve (Not Prior Submitter, Not Prior Auditor)
- An `Engineer` may `approve` a ChangeRequest provided they are NOT the
  engineer who submitted this request AND NOT the engineer who audited
  it.
- Concretely: permit `approve` when:
  - `prevSubmitter` is absent OR `principal != context.prevSubmitter`, AND
  - `prevAuditor` is absent OR `principal != context.prevAuditor`.

### 3. Audit (Not Prior Submitter, Not Prior Approver)
- An `Engineer` may `audit` a ChangeRequest provided they are NOT the
  engineer who submitted this request AND NOT the engineer who approved
  it.
- Concretely: permit `audit` when:
  - `prevSubmitter` is absent OR `principal != context.prevSubmitter`, AND
  - `prevApprover` is absent OR `principal != context.prevApprover`.

## Notes

- The three rules are pairwise symmetric: each action excludes the
  principal-identity of the OTHER two actions' prior actors. This is
  what makes the SoD strictly three-way.
- All three context attributes are optional (`?` in the schema). Any
  read of `context.prevX` MUST be guarded by `context has prevX` first
  (Cedar §8.3 — the type-checker does not propagate negation through
  `has`). Use the canonical positive form:
  `(!(context has prevX) || (context has prevX && context.prevX != principal))`.
- Common failure modes:
  - (a) Forgetting one of the two pairwise checks for an action,
    breaking the three-way invariant on one diagonal.
  - (b) Encoding only same-action exclusion (e.g. "same engineer can't
    submit twice") instead of cross-action exclusion.
  - (c) Writing `!(context has prevApprover) || context.prevApprover
    != principal` without the inner re-guard, which Cedar's
    type-checker rejects on negated `has`.
- An absent prev attribute means the corresponding action has not yet
  been performed, so no exclusion applies. The fresh-request floors
  exercise this case.
