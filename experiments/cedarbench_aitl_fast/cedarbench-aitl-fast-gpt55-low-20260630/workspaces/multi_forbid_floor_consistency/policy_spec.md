---
pattern: multi-forbid floor consistency
difficulty: hard
features:
  - multiple-global-forbids
  - floor-bound-consistency
  - context-attestation
  - boolean-conjunction-stress
domain: enterprise-access-control
synthesis_difficulty: 3
---

# Multi-Forbid Floor Consistency

## Pattern

A unified access-control policy that layers **four independent global
forbids** on top of permits. Every permit must be jointly satisfiable
with all four forbids — i.e., for any case where the user is supposed to
be permitted, none of the four forbid conditions may be triggered.

This scenario stress-tests §8.8 (floor-bound consistency) at the 4-way
boundary. A naïve floor like "owner permitted to access their resource"
will fail because it doesn't carve out the four forbid conditions.

## Entities

- `User`
  - `isSuspended: Bool` — disciplinary suspension blocks ALL access.
  - `mfaVerified: Bool` — whether the user completed MFA this session.
- `Resource`
  - `isClassified: Bool` — classified resources require MFA.
  - `requiresApproval: Bool` — flagged resources need an out-of-band
    approval attestation in the request context.

## Actions

- `access` — full read/write access to the resource.
- `view` — read-only metadata view; subject to fewer restrictions.

## Context

- `outsideBusinessHours: Bool` — request is outside 9–5 local time.
- `approvalGranted: Bool` — host application has verified an approval
  ticket for the resource and attests to it in the context.

## Four global forbids

These forbids apply across both actions unless noted:

1. **Suspension forbid (both actions).** Suspended users have no access
   to anything: `forbid when principal.isSuspended`.
2. **Outside-hours forbid (access only).** `access` is blocked outside
   business hours; `view` is allowed: `forbid when action == access &&
   context.outsideBusinessHours`.
3. **Classified-MFA forbid (both actions).** Classified resources
   require MFA: `forbid when resource.isClassified &&
   !principal.mfaVerified`.
4. **Approval-required forbid (access only).** Approval-flagged
   resources require an attestation: `forbid when action == access &&
   resource.requiresApproval && !context.approvalGranted`.

## Required permits (floors)

The policy MUST allow each of the following:

- Any user can `access` a non-classified, non-approval-flagged resource
  during business hours, when not suspended.
- Any user with MFA can `access` a classified, non-approval-flagged
  resource during business hours, when not suspended.
- Any user can `access` a non-classified, approval-flagged resource
  during business hours when an approval is attested and they are not
  suspended.
- Any user with MFA can `access` a classified, approval-flagged resource
  during business hours when an approval is attested and they are not
  suspended.
- Any user can `view` a non-classified resource regardless of business
  hours, when not suspended.
- Any user with MFA can `view` a classified resource regardless of
  business hours, when not suspended.

## Safety properties

- `access` is only ever permitted when ALL FOUR forbid conditions are
  absent: not suspended, in business hours, (not classified OR
  MFA-verified), (no approval required OR approval granted).
- `view` is only ever permitted when forbids 1 and 3 are absent:
  not suspended, (not classified OR MFA-verified). Forbids 2 and 4 do
  not apply to `view`.
