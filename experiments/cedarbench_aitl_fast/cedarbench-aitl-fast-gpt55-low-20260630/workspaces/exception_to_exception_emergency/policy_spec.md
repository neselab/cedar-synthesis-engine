---
pattern: nested emergency override chain
difficulty: hard
features:
  - layered exceptions
  - break-glass
  - security lockdown override
  - principal attribute gating
  - context-driven mode switching
domain: enterprise security
synthesis_difficulty: 4
---

# Exception-to-Exception Emergency — Policy Specification

## Context

This policy governs `User` access to `Resource` under three nested
operational tiers. The interesting structural property is that each tier
is itself an **exception** to the tier above it:

- Normal operations grant access.
- A **lockout** (Tier 1) suspends normal access.
- A **break-glass** (Tier 2) overrides the lockout for users who hold
  break-glass authorization.
- A **security lockdown** (Tier 3) overrides break-glass and denies
  everyone except users with explicit security clearance.

The common bug pattern this scenario stresses is failing to make Tier 3
trump Tier 2: a naive author might write the break-glass permit and the
lockdown forbid as independent rules and accidentally let
break-glass-authorized users punch through a lockdown.

## Entities

- `User` with attributes:
  - `role: String`
  - `hasBreakGlass: Bool` — pre-provisioned authorization to invoke
    break-glass when a lockout is active.
  - `securityClearance: Bool` — pre-provisioned clearance that survives
    a security lockdown.
- `Resource` (no attributes).

## Actions

- `access` — primary access action on a Resource.
- `securityOverride` — administrative action used by cleared personnel
  during a lockdown. Out of scope for the layered chain (it is only
  available to clearance holders); included to give the scenario two
  distinct actions.

## Context

- `lockoutActive: Bool`
- `breakGlassInvoked: Bool`
- `securityLockdownActive: Bool`

## Requirements

### 1. Normal operations
- When no operational tier is engaged, all users may `access` any
  Resource. Specifically, when `!context.lockoutActive`, the request is
  permitted.

### 2. Lockout suspends normal access (Tier 1)
- When `context.lockoutActive == true`, normal access is denied unless
  Tier 2 applies.

### 3. Break-glass override (Tier 2)
- A user MAY `access` a Resource during a lockout when ALL of:
  - `context.lockoutActive == true`, AND
  - `context.breakGlassInvoked == true`, AND
  - `principal.hasBreakGlass == true`.
- This is the second-tier exception: it carves out a permission inside
  the lockout regime.

### 4. Security lockdown trumps everything (Tier 3)
- When `context.securityLockdownActive == true`, ALL `access` is denied
  EXCEPT for users where `principal.securityClearance == true`.
- This rule **trumps Tier 2**. A user with `hasBreakGlass == true` and
  no `securityClearance` MUST NOT be able to access a Resource during a
  security lockdown, even if `breakGlassInvoked == true` and a lockout
  is also active. This is the structural invariant of the scenario.

### 5. securityOverride action
- Only users with `securityClearance == true` may invoke
  `securityOverride`. This action is unaffected by lockout/break-glass
  context. (Modeled as a separate ceiling so the dataset exercises
  multi-action policies.)

## Reference encoding

The intended Cedar policy is a single permit with both a `when` clause
(combining the normal and break-glass paths) and an `unless` clause
(implementing the security-lockdown trump):

```cedar
permit (
    principal is User,
    action == Action::"access",
    resource is Resource
)
when {
    !context.lockoutActive
    || (context.lockoutActive
        && context.breakGlassInvoked
        && principal.hasBreakGlass)
}
unless {
    context.securityLockdownActive && !principal.securityClearance
};
```

Note that the `unless` clause makes Tier 3 dominate Tier 2: even if the
break-glass branch of the `when` clause fires, the `unless` clause
denies the request whenever the lockdown is active and the user lacks
clearance.

## Notes
- Cedar denies by default. The single permit above grants the only
  `access` paths.
- §8.8 floor-bound consistency: every floor in this scenario must
  exclude the `securityLockdownActive && !securityClearance` case, since
  the global `unless` clause denies it. A floor that omits this guard
  would be unsatisfiable against any candidate that correctly implements
  Tier 3.
- The reference encoding deliberately exercises Cedar's `when ... unless`
  construct, which corresponds naturally to layered exceptions: `when`
  enumerates the permission paths, `unless` enumerates the dominating
  denials.
