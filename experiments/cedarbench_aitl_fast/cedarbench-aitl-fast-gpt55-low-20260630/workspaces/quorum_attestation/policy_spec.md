---
pattern: Emergency override quorum via Set.containsAll subset enumeration
difficulty: hard
features:
  - set containsAll for subset membership
  - threshold encoded as disjunction over subsets
  - no .size() operator workaround
  - emergency override pattern
domain: incident response / emergency override
synthesis_difficulty: 4
---

# Quorum Attestation — Emergency Override Policy Specification

## Context

This policy gates an **emergency override action** behind a 3-of-5
quorum of attesting approvers. Unlike scheduled multisig governance,
this is an **incident-response break-glass** pattern: when a
production system needs an emergency intervention, an operator
submits a request, and an off-Cedar attestation service collects
real-time approvals from the on-call approver pool.

An `EmergencyAction` resource has a fixed pool of 5 known
**eligible approvers** (`s1`, `s2`, `s3`, `s4`, `s5`) who may
attest to the emergency. When a request is made, the attestation
service supplies `context.attesters` — the set of approvers who
have actively confirmed the emergency. Executing the override
requires **at least 3 of the 5** eligible approvers to be in
`attesters`.

Cedar has **no `.size()` operator on sets**, so the threshold cannot
be written as `context.attesters.size() >= 3`. Instead, the policy
must enumerate the C(5,3) = 10 possible 3-element subsets of the
eligible-approver pool and check, via `.containsAll(...)`, whether
`attesters` is a superset of at least one of them.

## Entities

- **Approver** — represents an individual on-call approver. The
  five eligible approvers for any given emergency are referred to
  by entity ID `Approver::"s1"` through `Approver::"s5"` for this
  benchmark.
- **EmergencyAction** — the emergency override artifact.
  - `eligibleApprovers: Set<Approver>` — informational; the policy
    hard-codes the enumerated `Approver::"s1"` .. `Approver::"s5"`
    subsets.

## Context

For the `executeEmergency` action only:

| Attribute    | Type             | Meaning                                              |
|--------------|------------------|------------------------------------------------------|
| `attesters`  | `Set<Approver>`  | Approvers who have actively confirmed the emergency. |

`viewEmergency` takes an empty context.

## Actions

### 1. `executeEmergency`

Permitted when at least 3 of the 5 eligible approvers are in
`context.attesters`. The principal must itself be one of the five
eligible approvers (any of them may submit the execute request once
the quorum is met).

Encoding sketch:

```cedar
permit (
    principal is Approver,
    action == Action::"executeEmergency",
    resource is EmergencyAction
)
when {
    (principal == Approver::"s1" || principal == Approver::"s2"
     || principal == Approver::"s3" || principal == Approver::"s4"
     || principal == Approver::"s5")
    && (
        context.attesters.containsAll([Approver::"s1", Approver::"s2", Approver::"s3"])
     || context.attesters.containsAll([Approver::"s1", Approver::"s2", Approver::"s4"])
     || context.attesters.containsAll([Approver::"s1", Approver::"s2", Approver::"s5"])
     || context.attesters.containsAll([Approver::"s1", Approver::"s3", Approver::"s4"])
     || context.attesters.containsAll([Approver::"s1", Approver::"s3", Approver::"s5"])
     || context.attesters.containsAll([Approver::"s1", Approver::"s4", Approver::"s5"])
     || context.attesters.containsAll([Approver::"s2", Approver::"s3", Approver::"s4"])
     || context.attesters.containsAll([Approver::"s2", Approver::"s3", Approver::"s5"])
     || context.attesters.containsAll([Approver::"s2", Approver::"s4", Approver::"s5"])
     || context.attesters.containsAll([Approver::"s3", Approver::"s4", Approver::"s5"])
    )
};
```

### 2. `viewEmergency`

Permitted for **any** Approver (not just the eligible five). During
an incident, situational awareness is broadly distributed; viewing
the emergency record itself is not gated on eligibility, only on
being an Approver entity (i.e., logged in as on-call staff).

## Notes

- **Cedar set facts the candidate must respect:**
  - `set.contains(elem)` — single membership.
  - `set.containsAll(otherSet)` — subset.
  - `set.containsAny(otherSet)` — non-empty intersection.
  - There is **no `.size()` operator**.
  - `[].containsAll(anything) == true` (vacuous), so an empty
    attesters set still cannot satisfy any of the 10 disjuncts
    because each disjunct requires a non-empty subset.
- The failure modes the harness will hunt:
  1. Using `.contains` on a single hard-coded approver instead of
     `.containsAll` on a 3-element subset (under-permits).
  2. Using `.containsAny` over the full eligible set (over-permits —
     1 attester would satisfy it).
  3. Omitting one or more of the 10 subsets, which under-permits a
     specific quorum combination.
  4. Failing to gate executeEmergency on principal eligibility
     (any Approver could trigger an override given quorum) —
     ceiling violation.
