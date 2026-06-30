---
pattern: compound attestation multi-signer
difficulty: hard
features:
  - three optional context records
  - record-typed context attributes
  - distinct-signer constraints
  - per-attestation validity windows
  - 9-clause conjunction
domain: governance / multi-sig
synthesis_difficulty: 4
---

# Compound Attestation Multi-Signer — Policy Specification

## Context

This policy implements a **multi-signer governance gate** for executing
high-stakes proposals. Each `Proposal` declares a set of `requiredSigners`
(three users expected to attest). To `execute` the proposal, the request
context must carry **three independent attestations**, one per signer,
each currently within its own validity window. `view` is open to any user.

The challenge is that the encoding requires all three optional record
attributes (`attestation1`, `attestation2`, `attestation3`) to be
independently `has`-guarded before any of their fields are read. The
permitted-form check is a **nine-clause conjunction** with no single
point of failure: drop any clause and either a ceiling or a floor breaks.

## Entities

- **User** — no attributes; identity is the only thing that matters.
- **Proposal** — `requiredSigners: Set<User>` — the three signers who
  must attest before the proposal can execute.

## Actions

- **execute** — gated by the three-attestation conjunction (below).
- **view** — open to any user; no context required.

## Context attributes (execute only)

Three optional attestation records, plus the current time:

| Attribute       | Type                                                           |
|-----------------|----------------------------------------------------------------|
| `attestation1?` | `{ signer: User, signedAt: datetime, validUntil: datetime }`   |
| `attestation2?` | `{ signer: User, signedAt: datetime, validUntil: datetime }`   |
| `attestation3?` | `{ signer: User, signedAt: datetime, validUntil: datetime }`   |
| `now`           | `datetime`                                                     |

## Access rules

### 1. execute (governance gate)

`execute` is permitted on a `Proposal` if and only if **all** of the
following hold:

1. All three attestation records are present in context.
2. Each attestation's `signer` belongs to the proposal's `requiredSigners` set.
3. The three attestation `signer`s are pairwise distinct (no double-counting).
4. Each attestation's `validUntil` is at or after `context.now`.

### 2. view

Any `User` may `view` any `Proposal`. No context required.

## Notes

- All three attestation records are **optional** — every read must be
  preceded by a `has` guard. The negated-`has` trap (`!(context has X) ||
  context.X.field == ...`) is rejected by Cedar's typechecker; the safe
  form is `(!(context has X) || (context has X && context.X.field == ...))`,
  but for the `execute` permit the cleaner pattern is to require
  `context has attestation1 && context has attestation2 && context has
  attestation3` up front.
- Pairwise-distinct enforcement requires three explicit `!=` clauses;
  Cedar has no built-in cardinality operator on records.
- The policy intentionally encodes the conjunction in one permit rather
  than splitting per-signer. A candidate that drops any of the nine
  clauses (3 has-guards, 3 set-membership, 3 distinctness, 3 validity
  comparisons — minus the duplicates the floor exercises) will either
  permit a forbidden case (ceiling failure) or deny a required case
  (floor failure).
- Common failure modes: (a) forgetting one or more `has`-guards, leading
  to schema-validation failure; (b) omitting one of the three pairwise
  inequalities, allowing the same signer to attest twice; (c) checking
  `signedAt` instead of `validUntil`; (d) using `<` instead of `<=` on
  the validity comparison.
