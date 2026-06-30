---
pattern: anti-transitive delegation
difficulty: medium
features:
  - optional context attribute (`has` guarding)
  - depth-bounded delegation (no transitivity)
  - per-action scoping (delegate is owner-only)
  - record-typed context attribute
domain: legal / capability systems
synthesis_difficulty: 3
---

# Anti-Transitive Delegation — Policy Specification

## Context

This policy implements *non-transitive* access delegation on a
Resource. The Resource has an `owner` who may always act on it. The
owner may delegate `read`/`write` access to one other User — but the
delegate can NOT pass that access along to anyone else. The chain
must remain exactly one hop deep.

This pattern shows up in legal capability systems (notarized power of
attorney that disallows substitution), regulated environments
(contractor access that contractually may not be sub-contracted),
and security-sensitive APIs (per-session tokens that explicitly
forbid token re-issuance).

In production, the host application maintains the grant graph and,
for each incoming request, looks up "is there a pre-validated grant
from the resource owner to this principal?" If so, it attaches a
record to the request context as `delegationGrant`, including a
`depth` field that the host computed by walking the chain. A
direct owner→delegate grant has `depth == 1`; any longer chain
yields `depth >= 2`. The policy MUST refuse to honor anything
other than `depth == 1`.

Principal is `User`; resource is `Resource`. Three actions:
`read`, `write`, `delegate`.

## Requirements

### 1. Owner Baseline Access

- The resource's owner may always `read` and `write` the resource.
  Concretely: permit when `principal == resource.owner`. No grant
  lookup is needed.

### 2. Grant-Based Read/Write (Depth-1 Only)

- A non-owner User may `read` or `write` the Resource when ALL of
  the following hold:
  - The request's context includes a `delegationGrant` attribute
    (`context has delegationGrant`), AND
  - `context.delegationGrant.delegatee == principal`, AND
  - `context.delegationGrant.delegator == resource.owner` — the
    grant must originate from the resource's owner, not from some
    intermediate party, AND
  - `context.delegationGrant.resource == resource` — the grant must
    name THIS resource (no cross-resource confusion), AND
  - `context.delegationGrant.depth == 1` — exactly one hop. Any
    other depth (0, 2, 3, ...) MUST NOT confer access.

### 3. Delegate Action — Owner Only

- The `delegate` action represents the host-side capability of
  issuing a new grant. ONLY the resource's owner may perform it.
- Concretely: permit `delegate` when `principal == resource.owner`.
- The policy MUST NOT consult `context.delegationGrant` when
  evaluating `delegate`. If it did, a depth-1 delegate could request
  `delegate` and produce a depth-2 grant — defeating the entire
  point of the pattern. The simplest correct encoding is: just
  don't reference `delegationGrant` in the `delegate` permit at
  all. (This avoids the §8.6 role-intersection trap by using a
  positive permit gate rather than a negative forbid.)

## Notes

- The `delegationGrant` attribute is **optional** in the schema
  (declared with `?`). Per Cedar's type-checker, every read of
  `context.delegationGrant.X` must be guarded by
  `context has delegationGrant` in the same conjunct. A naive policy
  that reads `context.delegationGrant.delegatee` without the `has`
  guard will fail Cedar validation. (See §8.3 in
  `docs/harness_fix_log.md` for the negated-`has` trap.)
- The `depth == 1` check uses `==`, not `<= 1` or `>= 1`. A grant
  with `depth == 0` (which would represent the owner "delegating to
  themselves," a contradictory state the host should never produce)
  must also be refused. A grant with `depth >= 2` is a transitive
  chain and must be refused.
- The `delegate` action is a single action. Do NOT collapse it with
  `read`/`write` into a shared permit — they have different
  authorization rules.
- Common failure modes:
  (a) forgetting the `has` guard on the optional attribute;
  (b) using `<=` or `>=` on the depth check (admitting transitive
      chains or zero-depth states);
  (c) referencing `delegationGrant` in the `delegate` permit, which
      lets delegates re-delegate;
  (d) forgetting the `delegator == resource.owner` check, allowing a
      grant signed by some intermediate to be honored as if it came
      from the owner.
