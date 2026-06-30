---
pattern: N-of-M signature threshold with withdrawable signatures
difficulty: hard
features:
  - set containsAll for subset membership
  - threshold encoded as disjunction over subsets
  - no .size() operator workaround
  - withdrawable / dynamic context attestations
domain: governance / multi-sig
synthesis_difficulty: 4
---

# N-of-M Signature Withdrawal — Policy Specification

## Context

This policy implements a **3-of-5 multi-signature governance** scheme for
proposal execution. A `Proposal` has a fixed set of 5 known eligible
signers (`s1`, `s2`, `s3`, `s4`, `s5`). At any moment, an off-Cedar
signing service tracks which signers have signed AND not subsequently
withdrawn their signature; this dynamic set is provided to Cedar as
`context.activeSigners`. Executing the proposal requires that at least
**3 of the 5** eligible signers are currently in `activeSigners`.

Cedar has **no `.size()` operator on sets**, so the threshold cannot be
written as `context.activeSigners.size() >= 3`. Instead, the policy
must enumerate the C(5,3) = 10 possible 3-element subsets of the
eligible-signer set and check, via `.containsAll(...)`, whether
`activeSigners` is a superset of at least one of them.

## Entities

- **Signer** — represents an individual key-holder. The five eligible
  signers for any given proposal are referred to by entity ID
  `Signer::"s1"` through `Signer::"s5"` for this benchmark.
- **Proposal** — the governance artifact under consideration.
  - `requiredQuorum: Long` — fixed at `3` (informational; the threshold
    is encoded in the policy structure, not read from this attribute).
  - `eligibleSigners: Set<Signer>` — fixed at
    `{s1, s2, s3, s4, s5}` (informational; the policy hard-codes the
    enumerated subsets).

## Context

For the `executeProposal` action only:

| Attribute        | Type             | Meaning                                           |
|------------------|------------------|---------------------------------------------------|
| `activeSigners`  | `Set<Signer>`    | Signers who have signed AND not withdrawn.        |

Other actions take an empty context.

## Actions

### 1. `executeProposal`

Permitted when at least 3 of the 5 eligible signers are in
`context.activeSigners`. The principal must itself be one of the five
eligible signers (any of them may submit the execute request once the
quorum is met).

Encoding sketch:

```cedar
permit (
    principal is Signer,
    action == Action::"executeProposal",
    resource is Proposal
)
when {
    (principal == Signer::"s1" || principal == Signer::"s2"
     || principal == Signer::"s3" || principal == Signer::"s4"
     || principal == Signer::"s5")
    && (
        context.activeSigners.containsAll([Signer::"s1", Signer::"s2", Signer::"s3"])
     || context.activeSigners.containsAll([Signer::"s1", Signer::"s2", Signer::"s4"])
     || context.activeSigners.containsAll([Signer::"s1", Signer::"s2", Signer::"s5"])
     || context.activeSigners.containsAll([Signer::"s1", Signer::"s3", Signer::"s4"])
     || context.activeSigners.containsAll([Signer::"s1", Signer::"s3", Signer::"s5"])
     || context.activeSigners.containsAll([Signer::"s1", Signer::"s4", Signer::"s5"])
     || context.activeSigners.containsAll([Signer::"s2", Signer::"s3", Signer::"s4"])
     || context.activeSigners.containsAll([Signer::"s2", Signer::"s3", Signer::"s5"])
     || context.activeSigners.containsAll([Signer::"s2", Signer::"s4", Signer::"s5"])
     || context.activeSigners.containsAll([Signer::"s3", Signer::"s4", Signer::"s5"])
    )
};
```

### 2. `viewProposal`

Permitted for any of the five eligible signers. No quorum requirement,
no context attestations.

### 3. `addSignature`

Permitted for any of the five eligible signers. The off-Cedar signing
service is responsible for tracking the actual signed set; Cedar only
gates whether the principal is allowed to interact with the proposal
at all.

### 4. `withdrawSignature`

Permitted for any of the five eligible signers (a signer may always
withdraw their own signature; the host application enforces "you can
only withdraw your own").

## Notes

- **Cedar set facts the candidate must respect:**
  - `set.contains(elem)` — single membership.
  - `set.containsAll(otherSet)` — subset.
  - `set.containsAny(otherSet)` — non-empty intersection.
  - There is **no `.size()` operator**.
  - `[].containsAll(anything) == true` (vacuous), so an empty
    activeSigners set still cannot satisfy any of the 10 disjuncts
    because each disjunct requires a non-empty subset.
- The three-line failure modes the harness will hunt:
  1. Using `.contains` on a single hard-coded signer instead of
     `.containsAll` on a 3-element subset (under-permits).
  2. Using `.containsAny` over the full eligible set (over-permits —
     1 signer would satisfy it).
  3. Omitting one or more of the 10 subsets, which under-permits a
     specific quorum combination (e.g. dropping the {s3,s4,s5} disjunct
     denies execution when only s3, s4, s5 are active).
- Non-eligible principals (any `Signer` not in {s1..s5}) must NOT be
  able to view, sign, withdraw, or execute.
