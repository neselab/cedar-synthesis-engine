---
pattern: warehouse zone access
difficulty: medium
features:
  - zone-matching guard (string equality)
  - wildcard zone ("all") bypass
  - hazardous-item role escalation
  - action-specific role requirements
domain: logistics / warehouse
synthesis_difficulty: 3
---

# Inventory Warehouse Zone Access -- Policy Specification

## Context

A warehouse is divided into zones: `"receiving"`, `"storage"`, and
`"shipping"`. Workers are assigned to a single zone (or `"all"` for
roaming supervisors). Inventory items track their current zone. Access
to an item depends on whether the worker's assigned zone matches the
item's current zone. Hazardous items impose additional role requirements
on certain actions.

Principal is `Worker`; resource is `Inventory`. Workers have a `zone`
attribute (`"receiving"`, `"storage"`, `"shipping"`, or `"all"`) and a
`role` attribute (`"handler"` or `"supervisor"`). Three actions: `move`,
`inspect`, `dispose`.

## Requirements

### 1. Move (Zone Match + Hazardous Escalation)
- A worker may `move` an inventory item when the worker's zone matches
  the item's `currentZone`, OR the worker's zone is `"all"`.
- **Hazardous escalation:** if the item is hazardous (`isHazardous == true`),
  only a supervisor (`role == "supervisor"`) may move it. Handlers are
  never permitted to move hazardous items, even if their zone matches.
- Concretely: permit `move` when:
  - (`principal.zone == resource.currentZone` OR `principal.zone == "all"`), AND
  - (`resource.isHazardous == false` OR `principal.role == "supervisor"`).

### 2. Inspect (Zone Match Only)
- Any worker may `inspect` an inventory item when their zone matches
  the item's `currentZone`, or the worker's zone is `"all"`.
- There is no role restriction on inspection -- both handlers and
  supervisors may inspect.
- Concretely: permit `inspect` when:
  - `principal.zone == resource.currentZone` OR `principal.zone == "all"`.

### 3. Dispose (Supervisor + Zone Match)
- Only a `supervisor` may `dispose` of an inventory item, and only
  when their zone matches the item's `currentZone` or the worker's
  zone is `"all"`.
- Handlers are never permitted to dispose of any item, hazardous or not.
- Concretely: permit `dispose` when:
  - `principal.role == "supervisor"`, AND
  - (`principal.zone == resource.currentZone` OR `principal.zone == "all"`).

## Notes
- The hazardous-item restriction on `move` is NOT implemented as a
  forbid (per section 8.6 role-intersection trap). Instead, the permit
  for `move` directly encodes the condition that hazardous items require
  supervisor role. This avoids tripping a forbid that would block
  supervisors who are also in other roles.
- Zone `"all"` is a convenience designation for roaming supervisors.
  It acts as a wildcard match against any `currentZone`.
- There are no forbids in this policy. All restrictions are encoded
  as conditions on the permits.
