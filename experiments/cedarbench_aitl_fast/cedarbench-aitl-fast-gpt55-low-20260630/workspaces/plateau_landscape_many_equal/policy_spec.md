---
pattern: exactly-k-of-n threshold (plateau search landscape)
difficulty: hard
features:
  - boolean disjunction
  - exactly-k-of-n threshold
  - combinatorial enumeration
  - adversarial plateau landscape
domain: synthetic / search-landscape stress
synthesis_difficulty: 4
---

# Plateau Landscape: Exactly 3-of-5 Threshold

## Context

This scenario is an adversarial stress test of the harness's repair
signal. The semantic rule is simple to state but its Cedar encoding
requires a long disjunction with no algebraic shortcut, and the
verification plan is constructed so that many plausible candidate
policies have IDENTICAL failure counts but DIFFERENT failure
identities. There is no local gradient: dropping any one disjunct
breaks exactly one floor, and any one of the C(5,3) = 10 disjuncts is
"equally salient" without the harness's per-check counter-example
trace.

## Entities

- `User` with five independent boolean attributes
  `bool1`, `bool2`, `bool3`, `bool4`, `bool5`.
- `Resource` with no attributes.
- One action: `access`.

## Rule

A `User` is permitted to perform `access` on a `Resource` if and only
if EXACTLY three of the five booleans on the principal are true.

Cedar does not provide arithmetic over `Bool` and does not provide a
`count` aggregate over per-attribute reads, so this MUST be expanded
as a disjunction over the C(5,3) = 10 distinct 3-of-5 subsets. Each
disjunct asserts the chosen three booleans are true AND the other two
are false. Omitting either side (the positive conjuncts or the
explicit negations of the unselected pair) breaks the "exactly"
constraint and changes the satisfying set.

The 10 disjuncts (in lexicographic order over the chosen triple):

1. `b1 && b2 && b3 && !b4 && !b5`
2. `b1 && b2 && !b3 && b4 && !b5`
3. `b1 && b2 && !b3 && !b4 && b5`
4. `b1 && !b2 && b3 && b4 && !b5`
5. `b1 && !b2 && b3 && !b4 && b5`
6. `b1 && !b2 && !b3 && b4 && b5`
7. `!b1 && b2 && b3 && b4 && !b5`
8. `!b1 && b2 && b3 && !b4 && b5`
9. `!b1 && b2 && !b3 && b4 && b5`
10. `!b1 && !b2 && b3 && b4 && b5`

## Plateau structure (verification plan)

The verification plan is one ceiling plus five floors plus liveness.

- **Ceiling (`access_safety`)**: candidate must imply the full
  10-disjunct reference. A candidate that adds spurious permits
  (e.g. permitting at 2-of-5 or 4-of-5) is over-permissive and
  violates this ceiling.
- **Floor `floor_combo_123`**: a user with `(b1, b2, b3) = (T,T,T)`
  and `(b4, b5) = (F,F)` MUST be permitted. This pins disjunct 1.
- **Floor `floor_combo_145`**: pins disjunct 6 — `(b1, b4, b5) = (T,T,T)`,
  `(b2, b3) = (F,F)`.
- **Floor `floor_combo_234`**: pins disjunct 7 — `(b2, b3, b4) = (T,T,T)`,
  `(b1, b5) = (F,F)`.
- **Floor `floor_combo_245`**: pins disjunct 9 — `(b2, b4, b5) = (T,T,T)`,
  `(b1, b3) = (F,F)`.
- **Floor `floor_combo_345`**: pins disjunct 10 — `(b3, b4, b5) = (T,T,T)`,
  `(b1, b2) = (F,F)`.
- **Liveness `liveness_access`**: at least one
  `User`-`access`-`Resource` request is permitted.

The five floors target five of the ten disjuncts. A candidate that
drops a single disjunct corresponding to one of the five pinned
combinations fails exactly that one floor and passes the other four.
Different droppages yield the SAME failure count (1) but DIFFERENT
failure identities — the plateau the synthesizer must traverse without
a local gradient.

## Notes

- Cedar denies by default; absence of a permit at 2-of-5 or 4-of-5 is
  sufficient. No explicit `forbid` is needed.
- The disjuncts are mutually exclusive (each pins one specific 5-tuple
  truth assignment), so the disjunction is exact.
- This scenario tests whether the per-check counter-example trace
  (each failed floor surfaces the SPECIFIC 5-tuple it cares about)
  is enough signal for the synthesizer to identify the missing
  disjunct on each iteration, even when the failure count alone is
  uninformative.
