---
pattern: regression battery — all six harness contributions in one scenario
difficulty: hard
features:
  - multi-role principals (primaryRole + secondaryRoles set)
  - global block-list (isBlocked) — drives §8.8 floor consistency
  - optional MFA token in context (has-guard required) — §8.4
  - datetime + duration arithmetic with Go-style duration — §8.9
  - confidential gate naturally expressible as ternary — §8.11
  - ceilings + floors with opposite directions — §8.1
  - role-intersection forbid trap — §8.6
domain: regression-battery
synthesis_difficulty: 5
---

# Regression Battery — All Traps

## Purpose

A single scenario engineered so that every documented harness
contribution must fire for synthesis to converge. It packs one
trigger for each of:

- **§8.1** directional feedback (ceilings + floors pointing opposite ways)
- **§8.4** parse-vs-validation (optional context attribute, must be `has`-guarded)
- **§8.6** role-intersection trap (multi-role users; restriction encoded as forbid is wrong)
- **§8.8** floor-bound consistency (global forbid; every floor must respect it)
- **§8.9** datetime/duration syntax (Go-style `duration("21h")`; ISO 8601 must be rejected)
- **§8.11** ternary-operator detector (a rule that LLMs typically encode with `?:`)

If any one of these contributions regresses, this scenario fails.

## Domain

A document store with three roles (`admin`, `manager`, `contractor`),
classification levels (`public`, `confidential`), and time-bounded
documents that expire. The host application supplies a request-time
clock (`context.now`), a `graceWindow` duration applied to expiry, and
an optional MFA token (`context.mfaToken`) set only when the user
completed a fresh MFA challenge.

## Entities

- `User { primaryRole, secondaryRoles, isBlocked }`. A user is "in
  role R" iff `primaryRole == R` OR `secondaryRoles.contains(R)`.
- `Document { classification, owner, expiresAt }`.

## Context (per request)

- `now: datetime` — current request time.
- `graceWindow: duration` — Go-style duration; the document's
  effective expiry for `read`/`edit` is `expiresAt.offset(graceWindow)`.
  References use `duration("21h")`-style literals; ISO 8601
  (`duration("PT21H")`) is rejected by Cedar at parse time.
- `mfaToken?: String` — OPTIONAL. Present only after a fresh MFA
  challenge. Any reference to it MUST be `has`-guarded:
  `context has mfaToken && context.mfaToken != ""`.

## Global rule (drives §8.6 and §8.8)

**Blocked users are denied for every action.** A user with
`principal.isBlocked == true` may not `read`, `edit`, or `archive`
any document, ever. This is the only blanket forbid in the policy.

The "contractor restriction" below is NOT encoded as a blanket
forbid — see §8.6 note.

## Per-action requirements

### `read`

A user may `read` a Document when ALL of:

1. The user is not blocked: `!principal.isBlocked`.
2. Time check: `context.now < resource.expiresAt.offset(context.graceWindow)`.
3. Role-and-MFA gate (this is the §8.11 trigger):
   - If the document is **public**, the user is in role `admin`,
     `manager`, OR `contractor`.
   - If the document is **confidential**, the user is in role
     `admin` or `manager` (no MFA required); OR the user is in role
     `contractor` AND has a fresh MFA token
     (`context has mfaToken && context.mfaToken != ""`).
   - Equivalently: the user must hold one of the three roles, and
     **if the user is acting on the strength of being a contractor
     reading a confidential document**, MFA is required. (LLMs are
     tempted to write this as a chain of `?:` ternaries — the §8.11
     detector forces boolean logic.)

### `edit`

A user may `edit` a Document when ALL of:

1. The user is not blocked.
2. Time check (same grace window): `context.now < resource.expiresAt.offset(context.graceWindow)`.
3. The user is in role `admin` OR `manager`. Contractors cannot
   edit, regardless of MFA.

### `archive`

A user may `archive` a Document when ALL of:

1. The user is not blocked.
2. The document has expired (no grace): `context.now > resource.expiresAt`.
3. The user is in role `admin`. (Contractors and managers cannot
   archive; archive is admin-only and is intentionally available
   ONLY after expiry — this drives §8.1 directional feedback in
   the opposite direction from `read`/`edit`.)

## §8.6 — role-intersection note

Because users hold multiple roles via `secondaryRoles`, the
contractor restriction on `edit`/`archive` MUST NOT be encoded as a
forbid keyed on `primaryRole`:

```cedar
// WRONG — blocks contractor+manager users from editing.
forbid (principal, action == Action::"edit", resource)
when { principal.primaryRole == "contractor" };
```

A user with `primaryRole == "contractor"` and `secondaryRoles
.contains("manager")` is in the manager role and MUST be permitted
to edit. The correct pattern is to express the restriction as the
ABSENCE of a permit: `edit` permits only fire when the user is in
role admin OR manager (membership = primary OR secondary).

## §8.8 — floor-consistency note

The global "blocked users denied" forbid means EVERY floor must add
`!principal.isBlocked` to its `when` clause. A floor that says
"owners must always be able to read" without that exclusion is
unsatisfiable jointly with the global forbid and will be rejected.

## §8.9 — duration syntax note

The `graceWindow` context attribute is `duration`. References use
Go-style: `duration("21h")`, `duration("1h")`, `duration("0s")`,
`duration("-24h")`. ISO 8601 (`duration("PT21H")`, `duration("P1D")`)
is REJECTED at parse time.

## §8.4 — optional attribute note

`context.mfaToken` is declared `mfaToken?: String`. Every read of
it must be guarded:

```cedar
context has mfaToken && context.mfaToken != ""
```

A bare `context.mfaToken != ""` fails type-checking. Negated `has`
without re-asserting the positive `has` inside the disjunct also
fails (see §5.4 / §8.3).

## Notes

- The `archive` action is intentionally only available AFTER expiry,
  while `read`/`edit` are only available BEFORE expiry (modulo the
  grace window). This crosswise structure exercises §8.1 directional
  feedback — ceilings tighten contractor reads while floors loosen
  admin archives.
- Owners do NOT have any special permit on this policy beyond their
  role. (Ownership is tracked because §8.8 floor-consistency floors
  about owners must still respect `!principal.isBlocked`.)
