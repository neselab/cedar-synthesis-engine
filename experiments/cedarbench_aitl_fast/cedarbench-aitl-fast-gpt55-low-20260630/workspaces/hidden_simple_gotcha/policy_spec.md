---
pattern: hidden creator-retention invariant
difficulty: hard (planning)
features:
  - dual ownership fields (creator vs currentOwner)
  - implicit invariant from schema design
  - adversarial spec phrasing
domain: file storage / collaboration
synthesis_difficulty: 4
---

# Hidden Simple Gotcha -- Policy Specification

## Context

This policy models a file-storage system where files have two distinct
ownership-related attributes:
- `creator`: the User who originally created the file. Immutable.
- `currentOwner`: the User who currently holds the file. Mutable via
  the `transfer` action.

These two fields are deliberately separate. In the system's data model,
ownership transfers update `currentOwner` only; `creator` is set once
at file-creation time and never changes thereafter.

## Requirements

### 1. read -- Owner OR Creator

A User may `read` a File when EITHER of the following holds:
- The User is the current owner (`principal == resource.currentOwner`), OR
- The User is the original creator (`principal == resource.creator`).

The creator retains a permanent read backdoor on every file they
created, even after ownership transfers away. This is intentional: the
business invariant is that creators can always look back at what they
made, so an audit/recovery path always exists through the creator.

### 2. transfer -- Current Owner Only

A User may `transfer` a File only when:
- The User is the current owner (`principal == resource.currentOwner`).

Critically, the creator does NOT have transfer rights once they are no
longer the current owner. The creator cannot reclaim the file they
created; only the present holder can hand it off.

## Notes -- Common Failure Mode

This spec is adversarially phrased. A surface reading of "users can
read files they own" leads naturally to writing only
`principal == resource.currentOwner` for `read`. That reading is wrong:
it ignores the creator-retention invariant implied by the existence of
two separate fields (`creator` vs `currentOwner`). If `creator` were
not meant to be read-relevant, the schema would not carry it.

The synthesizer is expected to notice the dual fields and infer that
creator-read is part of the contract. The floor `floor_creator_read`
exists exactly to catch this elision.

For `transfer`, the inverse is true: only `currentOwner` matters. A
synthesizer that "symmetrically" adds creator-transfer rights would
violate the `transfer_safety` ceiling.

## Notes -- Cedar mechanics

- No global forbids; floors need no exclusion clauses (per section 8.8).
- All conditions are simple equality comparisons on attributes -- no
  Set membership, no datetime, no optional context.
- The challenge is purely in spec interpretation, not Cedar syntax.
