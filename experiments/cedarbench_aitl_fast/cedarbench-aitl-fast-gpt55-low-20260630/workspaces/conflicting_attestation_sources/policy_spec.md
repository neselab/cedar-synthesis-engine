---
pattern: conflicting attestation sources (system-of-record vs request-claimed)
difficulty: hard
features:
  - optional context attribute
  - has-guard
  - cross-source consistency check
  - all-three-must-agree predicate
domain: document management / data governance
synthesis_difficulty: 3
---

# Conflicting Attestation Sources -- Policy Specification

## Context

Many production access systems consult more than one source for the same
underlying fact (e.g. who owns a record). The system-of-record stores
authoritative ownership on the resource itself, while the calling
client may *also* assert the same fact in the request context (often
because an upstream service believes it knows the answer faster than a
fresh DB read).

This policy hardens the access decision against the case where those
two sources disagree. The rule of thumb: if both sources speak, they
MUST agree. A silent context (no claim made) is fine; a present but
divergent claim is treated as a tampering / staleness signal and the
request is denied.

Entities: `User`, `Document` (with `recordedOwner: User`, the
system-of-record owner). Context: `now: datetime`, `claimedOwner?: User`
(an optional assertion of who the caller believes owns the document).

Actions: `view`, `transfer`. Both actions consult `recordedOwner` as
the ground truth, but `transfer` is more tightly bound: it requires
the caller to have *actively* asserted ownership in the request, and
that assertion must agree with the recorded owner and the principal
must be that owner.

## Requirements

### 1. View (Permit)
- A User may `view` a Document if and only if:
  - `principal == resource.recordedOwner`, AND
  - either `context.claimedOwner` is **absent**, OR
    `context.claimedOwner == resource.recordedOwner` (i.e. if the
    caller asserted an owner, the assertion agrees with the
    system-of-record).
- Concretely, divergence (`claimedOwner` present but not equal to
  `recordedOwner`) MUST cause the view request to be denied even when
  the principal is in fact the recorded owner. Divergence is treated
  as a tampering / cache-staleness signal.

### 2. Transfer (Permit)
- A User may `transfer` a Document if and only if all three of the
  following agree:
  - `context.claimedOwner` is **present** (transfer cannot proceed on
    silence -- the caller must affirmatively attest ownership), AND
  - `context.claimedOwner == resource.recordedOwner`, AND
  - `principal == resource.recordedOwner`.
- Equivalently: principal, recordedOwner, and the (mandatorily
  present) claimedOwner must be the same User.

## Cedar Encoding Notes

`claimedOwner` is declared with `?` in the schema, making it an
optional context attribute. Per harness rule §8.3, every read of an
optional attribute MUST be `has`-guarded. The "if present, must
match" semantics is the trap: writing
`!(context has claimedOwner) || context.claimedOwner == ...` is
rejected by Cedar's type-checker because negation does not propagate
through `has`. The correct guard is:

```
permit (...) when {
    principal == resource.recordedOwner
    && (
        !(context has claimedOwner)
        || (context has claimedOwner && context.claimedOwner == resource.recordedOwner)
    )
};
```

For `transfer`, both conjuncts of the existential branch are
required, so the guard collapses to:

```
permit (...) when {
    context has claimedOwner
    && context.claimedOwner == resource.recordedOwner
    && principal == resource.recordedOwner
};
```

## Notes
- Cedar denies by default, so no explicit forbid is needed for
  divergent or unauthorised requests; the absence of a satisfying
  permit is sufficient.
- The two actions have different "silence" semantics on purpose:
  `view` treats absence of claim as fine (legacy callers that don't
  know to attest), while `transfer` treats absence as disqualifying
  (high-risk action, must attest).
