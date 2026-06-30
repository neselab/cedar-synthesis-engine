---
pattern: hedging language without defined exceptions
difficulty: medium (planner discipline)
features:
  - owner-equality permit
  - hedging language ("normally", "rare exceptions")
  - planner-discipline test
domain: profile / identity management
synthesis_difficulty: 2
---

# Hypothetical Exception (Unspecified) — Policy Specification

## Context

This policy governs read access to user `Profile` resources. The
business owner has written the spec in informal English with hedging
language that hints at the existence of exceptions but does NOT define
them. The Phase 1 planner's job is to encode ONLY what the spec
actually says — not to invent exception paths the spec has not
authorized.

## Requirements

### 1. Self Profile Read

Users can **normally** view their own profile. Exceptions are rare and
handled separately by the security team out-of-band; they are NOT part
of this policy.

Concretely: permit `viewProfile` when `principal == resource.owner`.

## Anti-Requirements (planner discipline)

The phrasing "normally" and "rare exceptions ... handled separately"
is hedging language that tempts a planner to encode an exception path
such as:

- `permit when principal == resource.owner && !context.securityHold`
- `permit when principal == resource.owner unless context.frozen`
- `permit when principal == resource.owner && context.attestation == "ok"`

**None of these are correct.** The spec has not defined any such
attribute. The security-team workflow is explicitly described as
out-of-band. The policy must encode the literal rule:

```
permit when principal == resource.owner
```

with no extra conditions. Any candidate that adds an unspecified
exception attribute is more restrictive than the ceiling and will be
caught by the floor.

## Notes

- This scenario tests a meta-discipline of the planner / synthesizer:
  resisting the temptation to over-encode hedging language as
  invented attributes.
- The schema deliberately does NOT declare any optional context
  attributes for "exceptions" — there is nothing for a tempted
  planner to legitimately reference.
- The ceiling and the floor are the SAME literal policy:
  `permit when principal == resource.owner`. This makes the bound
  range a single point — the candidate must encode exactly this
  rule, no more permissive and no more restrictive.
