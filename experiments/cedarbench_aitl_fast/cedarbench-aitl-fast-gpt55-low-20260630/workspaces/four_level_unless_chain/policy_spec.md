---
pattern: four-level unless chain (deeply nested conditional denial)
difficulty: hard
features:
  - deeply nested conditional logic
  - "unless A unless B unless C unless D" override chain
  - boolean encoding of nested if/else (no Cedar ternary)
  - role + context conjunction
domain: emergency response / security lockdown
synthesis_difficulty: 4
---

# Four-Level Unless Chain — Emergency Lockdown Override

## Context

This policy governs an **emergency response platform** whose resources can
be progressively locked and progressively unlocked by chained authorities.
Cedar only supports a single `unless` clause per policy (one negation
layer), so a four-level English description of the form

> *normally permitted, but if X then forbidden, but if Y then permitted
> again, but if Z then permitted again, but if W then forbidden no matter
> what (except hasOverride).*

must be flattened into pure boolean logic inside one `permit ... when {...}
unless {...}` block. The natural translation invites a ternary / `if-then-else`
syntax, which Cedar does not support — the synthesizer must encode the
chain as disjunctions and conjunctions only.

## Entities

- **User**
  - `role: String` — one of `"user"`, `"responder"`, `"lead"`,
    `"commander"`.
  - `hasEmergencyAuth: Bool` — pre-attested emergency-response credential.
  - `hasOverride: Bool` — red-cell override token (very rare, only issued
    to incident commanders during cleared drills).
- **Resource**
  - `isLocked: Bool` — informational; not used in access logic.
  - `securityHold: Bool` — informational; not used in access logic.

## Context attributes

| Attribute                    | Meaning                                              |
|------------------------------|------------------------------------------------------|
| `lockoutActive`              | Platform-wide lockout has been declared.             |
| `emergencyMode`              | A graded emergency has been declared.                |
| `commanderOverrideActive`    | A commander-level override window is open.           |
| `redCellLockdown`            | Red-cell lockdown — overrides everything except `hasOverride`. |

## Actions

### 1. `access` — read/interact with the resource

The four-level English statement is:

> Permit `access` normally, **unless** `lockoutActive` is true, **unless**
> the user has `hasEmergencyAuth` and `emergencyMode` is true (which
> re-enables access), **unless** the user is a `commander` and
> `commanderOverrideActive` is true (which also re-enables access),
> **unless** `redCellLockdown` is true and the user does **not** have
> `hasOverride` (which forbids again no matter what).

Encoded as a single Cedar `permit ... when {...} unless {...}`:

```cedar
permit (
    principal is User,
    action == Action::"access",
    resource is Resource
)
when {
    !context.lockoutActive
    || (context.emergencyMode && principal.hasEmergencyAuth)
    || (context.commanderOverrideActive && principal.role == "commander")
}
unless {
    context.redCellLockdown && !principal.hasOverride
};
```

The `when` clause is the disjunction of the three "permitted again" cases
(plus the base "no lockout" case). The `unless` clause is the single
final lockdown that supersedes everything **except** `hasOverride`.

### 2. `forceAccess` — emergency forced access

Only a `commander` with `hasOverride == true` may `forceAccess`,
regardless of any lockout, emergency, or red-cell flags.

```cedar
permit (
    principal is User,
    action == Action::"forceAccess",
    resource is Resource
)
when {
    principal.role == "commander" && principal.hasOverride
};
```

## Notes

- **§8.11 trap.** The "if X then Y else Z" structure invites a ternary
  expression. Cedar does not have a ternary operator; the only legal
  encoding is boolean composition.
- **§8.8 trap.** Every `access` floor must be jointly satisfiable with
  the `unless { redCellLockdown && !hasOverride }` ceiling — i.e. each
  floor must explicitly assert either `!context.redCellLockdown` or
  `principal.hasOverride`. A floor that ignores the red-cell condition
  will conflict with the ceiling under symbolic analysis.
- The four resource attrs (`isLocked`, `securityHold`) are intentionally
  inert decoys — they appear in the schema but the rules do not depend
  on them. A naive synthesizer may try to gate on them; a correct
  synthesizer ignores them.
- Common failure modes: (a) using ternary / if-then-else syntax,
  (b) forgetting that `commanderOverrideActive` re-permits even when
  `lockoutActive` is set, (c) treating `redCellLockdown` as just another
  disjunct in the `when` clause instead of a hard `unless`,
  (d) writing floors that are inconsistent with the red-cell ceiling.
