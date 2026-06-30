---
pattern: ordered override resolution
difficulty: hard
features:
  - rule precedence ordering
  - optional principal attribute (customQuota)
  - guard-encoded priority (no native rule priorities)
  - tier-based defaults with overrides
domain: API quota / billing
synthesis_difficulty: 3
---

# Ordered Override Resolution -- Policy Specification

## Context

This policy governs whether a `User` may `call` a `Service`, where the
allowed request volume is determined by THREE rules with explicit
precedence ordering. Cedar has no native rule priorities -- all `permit`
clauses union together -- so precedence MUST be simulated via explicit
guards on the lower-priority rules ("apply Rule N only if no
higher-priority rule applies").

The scenario tests whether the synthesizer can correctly encode an
ordered override chain in Cedar's union semantics.

## Entities

- **User** -- the principal. Attributes:
  - `tier` (String) -- one of `"free"`, `"pro"`, `"enterprise"`.
  - `customQuota` (Long, OPTIONAL) -- a per-user override quota. When
    present, takes precedence over BOTH the tier-default and the
    enterprise-unlimited rule.
- **Service** -- the resource. No attributes used by the policy.

## Actions

- **call** -- invoke the service. Context provides `requestCount: Long`
  (the user's current request count for this billing window).

## Rules (precedence ORDER matters)

### Rule 1 (HIGHEST priority) -- per-user custom quota
If `principal has customQuota`, then the call is permitted iff
`context.requestCount < principal.customQuota`. This rule overrides
EVERYTHING below: an enterprise user with `customQuota = 5` is capped
at 5, NOT unlimited. A free user with `customQuota = 1000` gets 1000,
not the free-tier 10.

### Rule 2 (MEDIUM priority) -- enterprise unlimited
If `!(principal has customQuota)` AND `principal.tier == "enterprise"`,
the call is permitted with no rate limit.

### Rule 3 (LOWEST priority) -- tier defaults
If `!(principal has customQuota)` AND `principal.tier != "enterprise"`,
then:

| Tier   | Permitted when                |
|--------|-------------------------------|
| free   | requestCount < 10             |
| pro    | requestCount < 100            |
| (other tier values: never permitted) |

## Cedar encoding pattern

Because Cedar policies UNION their `permit` clauses, the lower rules
must be guarded with the negation of the higher-priority conditions.
The expected ceiling is a single permit with a disjunction of the
three priority-guarded branches:

```
permit (
    principal is User,
    action == Action::"call",
    resource is Service
)
when {
    // Rule 1 (highest) -- custom quota overrides everything
    (principal has customQuota
        && context.requestCount < principal.customQuota)
    // Rule 2 (medium) -- enterprise unlimited, but only if no custom quota
    || (!(principal has customQuota)
        && principal.tier == "enterprise")
    // Rule 3 (lowest) -- tier defaults, only if neither above applies
    || (!(principal has customQuota)
        && principal.tier == "free"
        && context.requestCount < 10)
    || (!(principal has customQuota)
        && principal.tier == "pro"
        && context.requestCount < 100)
};
```

## Notes

- `customQuota` is optional on the **principal** (User), not on the
  context. Every read MUST be `has`-guarded (per harness fix log §8.3).
- Strict less-than is used throughout: `requestCount == customQuota` is
  denied.
- A user whose tier is none of `"free"`, `"pro"`, `"enterprise"` and who
  has no `customQuota` is denied for any request count.
- Common failure modes: (a) Rule 1 not guarded with `has`-check on
  `customQuota`; (b) Rule 3 omits `!(principal has customQuota)` so a
  free user with `customQuota = 1000` is incorrectly capped at 10;
  (c) Rule 2 omits the customQuota negation so an enterprise user with
  a tight `customQuota` is incorrectly granted unlimited access.
