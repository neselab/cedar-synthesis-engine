---
pattern: five-way role intersection with multi-role principals
difficulty: hard
features:
  - multi-role principals (primary role + secondary roles set)
  - per-role permit structure (no role-keyed forbids)
  - resource-category gating
  - escalation-chain action
  - §8.6 role-intersection trap stress test
domain: enterprise-iam
synthesis_difficulty: 4
---

# Five-Way Role Intersection — Policy Specification

## Context

This policy governs a multi-role enterprise IAM pattern. Unlike the
classic "one user, one role" model, a `User` here has BOTH a primary
`role: String` and a `secondaryRoles: Set<String>`. A user can therefore
belong to multiple roles simultaneously (e.g. a developer who also holds
"qa", or an admin who also moonlights as an auditor). Role membership is
the **union** of the primary role and the secondary roles.

Five roles exist: `"admin"`, `"auditor"`, `"developer"`, `"qa"`, `"support"`.
Every `Resource` has a `category: String` (one of `"code"`, `"logs"`,
`"tickets"`, `"config"`). Five actions: `read`, `modify`, `delete`,
`audit`, `escalate`.

**Critical construction rule.** Because users hold multiple roles, the
policy MUST NOT use `forbid` rules keyed on a single role (e.g.
`forbid when { principal.role == "qa" }`) to block access. Doing so
would incorrectly block a user who is BOTH qa AND admin from an
admin-authorized action. The correct pattern is **per-role permits**:
write one `permit` rule per (role, action, category) cell and rely on
Cedar's default-deny to block everything else. A user in multiple roles
gets the **union** of their per-role permits.

## Requirements

### 1. Read (Permit — per-role, per-category)

A User may `read` a Resource under these role-keyed rules (each rule
fires independently; users in multiple roles get the union):

- **admin** may read any category.
- **auditor** may read any category (auditors need full visibility for
  compliance).
- **developer** may read `"code"` and `"logs"`. Developers may NOT read
  `"tickets"` or `"config"` on the strength of being a developer alone.
- **qa** may read `"code"` and `"tickets"`. QA may NOT read `"logs"` or
  `"config"` on the strength of being qa alone.
- **support** may read `"tickets"` only. Support may NOT read `"code"`,
  `"logs"`, or `"config"` on the strength of being support alone.

A user who holds, say, primary role `"support"` and a secondary role of
`"developer"` gets BOTH sets of permits and can therefore read
`"tickets"` (via support) AND `"code"` and `"logs"` (via developer).

### 2. Modify (Permit — per-role, per-category)

- **admin** may modify any category.
- **developer** may modify `"code"` and `"config"`.
- **qa** may modify `"tickets"` only.
- `auditor` and `support` have no modify permits on the strength of
  those roles alone.

### 3. Delete (Permit — admin only)

- **admin** may `delete` any category.
- No other role has a delete permit on its own. A user can only delete
  if they hold the `"admin"` role (either as primary or in
  `secondaryRoles`).

### 4. Audit (Permit — per-role, per-category)

- **auditor** may `audit` any category.
- **developer** may `audit` `"logs"` only (developers need to audit
  their own service logs, but nothing else).
- No other role has an audit permit.

### 5. Escalate (Permit — per-role escalation chain)

The `escalate` action represents handing a request up a support
hierarchy. The chain is:

    support → qa → developer → admin

Each link is a SEPARATE per-role permit:

- **support** may `escalate` a Resource of any category (escalates up
  to qa).
- **qa** may `escalate` a Resource of any category (escalates up to
  developer).
- **developer** may `escalate` a Resource of any category (escalates up
  to admin).
- `admin` and `auditor` have no `escalate` permit (admin is the top of
  the chain; auditor is off-chain).

(The destination of the escalation is not modeled in Cedar — it is a
host-application concern. From Cedar's standpoint, `escalate` is just
an action that requires the principal to hold one of the three chain
roles.)

## Membership Test

A user is considered to be in role `R` iff `principal.role == R` OR
`principal.secondaryRoles.contains(R)`. Every per-role permit rule MUST
use this union test, so that secondary-role holders get the same access
as primary-role holders.

## Notes

- Cedar denies by default. The per-role permits above are exhaustive:
  any (principal, action, resource) tuple that does not match at least
  one permit is denied.
- **Do not write role-keyed forbids.** A rule like
  `forbid when { principal.role == "support" }` would incorrectly
  block a user who is *both* support and admin from admin-authorized
  actions. The per-role-permit structure makes role-keyed forbids
  unnecessary and unsafe.
- **Do not write `!(principal.role == X)` guards.** Same trap — the
  guard ignores the secondary roles.
- The schema uses `Set<String>` for `secondaryRoles`. Use
  `principal.secondaryRoles.contains("admin")` for the test; `in` does
  not apply to Set<String>.
- Common pitfalls: forgetting to check `secondaryRoles` (only looking
  at `principal.role`), using role-keyed forbids to encode
  "blocked from X" (triggers §8.6), or collapsing multiple per-role
  permits into a single permit with a disjunction that accidentally
  drops a category constraint.
