---
pattern: contradictory requirements with explicit precedence resolution / §8.8 stress test
difficulty: hard (planning)
features:
  - explicit contradiction in spec
  - precedence-based resolution rule
  - quarantine forbid
  - owner baseline permit
domain: document storage / content moderation
synthesis_difficulty: 4
---

# Contradicting Requirements (Literal) — Policy Specification

## Context

This policy governs `view` access to Documents in a document storage
system. The spec contains TWO requirements that the writer was aware
would conflict in some cases. Rather than rewrite the spec to remove
the conflict, the writer included an explicit precedence rule.

A Phase 1 planner that mechanically translates each requirement into
a floor will produce jointly unsatisfiable bounds. The correct
behavior is to recognize the precedence rule and carve out the
contradicting cases from the weaker requirement's floor.

## Requirements

### Requirement A — Owner Read Access
- **Owners must always be able to view their own documents.**
- Concretely: `principal == resource.owner` should imply permission to
  `view` the document.

### Requirement B — Quarantine Block
- **Documents marked as `quarantined` must NEVER be viewable by anyone.**
- Concretely: `resource.quarantined == true` should imply denial,
  regardless of who the principal is — including the owner.

### Precedence Rule
- **When requirements conflict, security forbids take precedence over
  access permits. Quarantine overrides ownership.**
- An owner whose own document has been quarantined is NOT entitled to
  view it. The owner can request that quarantine be lifted (out of
  scope for this policy), but until then, the document is unreadable.

### Requirement C — Restated Owner Guarantee (post-resolution)
- After applying the precedence rule, the residual owner guarantee
  is: **for any document that is NOT quarantined, the owner may view
  it.** This is the form the policy must encode.
- This restatement exists to make the post-resolution guarantee
  explicit and to give a second independent verification angle on
  the resolved owner-permission property.

## Notes

- This spec is deliberately self-contradictory at the literal level
  in §A vs. §B. Requirement A says "always" and Requirement B says
  "never," and they meet on `principal == resource.owner &&
  resource.quarantined`. The precedence rule is what disambiguates.
- Per §8.8 floor-bound consistency, the planner must encode the
  resolved policy, not the literal requirements. Specifically:
  - The ceiling for `view` must exclude quarantined documents.
  - Every owner floor must be carved out by `!resource.quarantined` —
    NOT `permit when principal == resource.owner` standalone.
  - There must be NO floor that asserts "owner can view quarantined
    document." Such a floor would be jointly unsatisfiable with the
    quarantine ceiling.
- A naive planner that writes a `floor_owner` of just
  `permit when principal == resource.owner` will produce
  unsatisfiable bounds the moment the candidate respects the
  quarantine forbid (which it must, to satisfy the ceiling).
