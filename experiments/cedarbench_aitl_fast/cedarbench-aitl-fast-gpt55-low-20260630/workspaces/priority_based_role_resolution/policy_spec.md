---
pattern: priority-based role resolution
difficulty: medium
features:
  - multi-role users
  - tiered resources
  - additive permit composition
  - no-forbid encoding (role-intersection trap)
domain: content access
synthesis_difficulty: 3
---

# Priority-Based Role Resolution — Policy Specification

## Context

This policy governs access to a content library where Users can hold
**multiple roles simultaneously** (`user.roles: Set<String>`). Records
are tagged with a sensitivity `tier` (one of `"public"`, `"confidential"`,
`"premium-only"`, `"admin-only"`). Different roles have different
access rules per tier, with an explicit **role priority** ordering:

    admin  >  premium  >  subscriber  >  guest

A user who holds multiple roles is governed by the rule of the
**highest-priority role they hold**. For example, a user holding both
`{guest, subscriber}` should be treated as a subscriber (and gain
access to confidential records), even though a guest by itself cannot
view confidential records.

Cedar has no native rule-priority mechanism. Authors must simulate
priority by structuring their permits carefully.

## Roles and their per-tier access

The matrix below specifies which (role, action, tier) combinations
must be permitted. A user is granted access if **any role they hold**
has a permit for the (action, tier).

### viewRecord
| Role       | public | confidential | premium-only | admin-only |
|------------|--------|--------------|--------------|------------|
| guest      | yes    | no           | no           | no         |
| subscriber | yes    | yes          | no           | no         |
| premium    | yes    | yes          | yes          | no         |
| admin      | yes    | yes          | yes          | yes        |

### editRecord
| Role       | public | confidential | premium-only | admin-only |
|------------|--------|--------------|--------------|------------|
| guest      | no     | no           | no           | no         |
| subscriber | no     | no           | no           | no         |
| premium    | no     | no           | no           | no         |
| admin      | yes    | yes          | yes          | yes        |

### deleteRecord
| Role       | public | confidential | premium-only | admin-only |
|------------|--------|--------------|--------------|------------|
| guest      | no     | no           | no           | no         |
| subscriber | no     | no           | no           | no         |
| premium    | no     | no           | no           | no         |
| admin      | yes    | yes          | yes          | yes        |

## How to encode priority correctly in Cedar

The natural Cedar idiom: write **positive permits** for each role's
allowed (action, tier) combinations. Cedar's rule semantics are
**additive (union)** — if any rule permits the request, the request
is permitted. A user holding `{guest, subscriber}` who tries to view
a confidential record will match the subscriber permit, so they are
permitted — exactly what role-priority semantics require.

## What NOT to do — the role-intersection trap

Do **NOT** encode the priority by writing `forbid` rules keyed on the
lower-priority role. For example, the following is wrong:

    // WRONG — blocks subscriber-AND-guest users from confidential records
    forbid (principal, action == Action::"viewRecord", resource)
    when {
        principal.roles.contains("guest")
        && resource.tier == "confidential"
    };

A user holding both `"guest"` and `"subscriber"` would hit this
forbid even though their subscriber role should permit the access.
Cedar evaluates permits and forbids on the principal as a whole —
holding role X plus role Y triggers the forbid keyed on X regardless
of what Y permits. (See `harness_fix_log.md` §8.6.)

The correct encoding uses positive permits only — each permit grants
a specific role its specific access set, and the union of permits
over all roles a user holds yields the highest-priority outcome
automatically.

## Notes
- All roles are stored as strings in `principal.roles`; use
  `principal.roles.contains("admin")`, etc.
- Resource tiers are strings on `resource.tier`; compare with `==`.
- There are no context-dependent rules in this scenario — the policy
  is purely a function of the principal's roles and the resource's
  tier.
- A user with no recognized role (e.g. empty roles set) is not
  permitted any action. Cedar's deny-by-default handles this.
