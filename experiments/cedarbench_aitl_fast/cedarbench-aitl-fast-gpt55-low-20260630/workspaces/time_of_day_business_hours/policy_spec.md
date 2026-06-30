---
pattern: time-of-day business hours
difficulty: medium
features:
  - duration comparison for time-of-day
  - role-based override
domain: enterprise / HR
synthesis_difficulty: 2
---

# Time-of-Day Business Hours -- Policy Specification

## Context

This policy governs access to an enterprise system based on the time of
day and the user's role. The system models a common enterprise pattern:
ordinary employees can only work during business hours, while managers
and admins have extended access. A separate maintenance action is
restricted to admins during off-hours only.

Entities: `User` (with `role: String`) and `System`. The context carries
`currentHour: Long` representing the current hour (0-23) in 24-hour
format. Business hours are defined as 9:00 through 16:59 (i.e.,
`currentHour >= 9` AND `currentHour < 17`).

Two actions: `access` (general system access) and `maintenance`
(system maintenance tasks).

## Requirements

### 1. Employee Business-Hours Access (Permit)
- A User whose `role` is `"employee"` may perform the `access` action
  on a System resource ONLY during business hours: `context.currentHour
  >= 9` AND `context.currentHour < 17`.
- Employees may NOT access the system outside of business hours.

### 2. Manager and Admin Anytime Access (Permit)
- A User whose `role` is `"manager"` or `"admin"` may perform the
  `access` action on a System resource at any hour, with no time-of-day
  restriction.

### 3. Admin Off-Hours Maintenance (Permit)
- A User whose `role` is `"admin"` may perform the `maintenance` action
  on a System resource ONLY outside of business hours: `context.currentHour
  < 9` OR `context.currentHour >= 17`.
- Only admins may perform maintenance. Employees and managers are never
  permitted to perform maintenance regardless of the time.

### 4. Maintenance During Business Hours -- Forbidden
- No user, regardless of role, may perform the `maintenance` action
  during business hours (when `context.currentHour >= 9` AND
  `context.currentHour < 17`). This prevents maintenance windows from
  disrupting active users.

## Notes
- `currentHour` is a Long in the range 0-23. The host application is
  responsible for populating this value from the server clock.
- Business hours are defined as hours 9 through 16 inclusive (i.e.,
  9:00 AM to 4:59 PM). Hour 17 (5:00 PM) is outside business hours.
- Cedar denies by default, so the absence of a permit for employees
  outside business hours or for non-admin maintenance is sufficient.
  An explicit forbid for maintenance during business hours provides
  defense-in-depth.
- The role values are exactly `"employee"`, `"manager"`, and `"admin"`.
  No other roles exist in this system.
