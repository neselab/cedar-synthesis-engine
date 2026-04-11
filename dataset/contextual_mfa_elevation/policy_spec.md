# Contextual MFA Elevation — Policy Specification

## Context

This policy implements **step-up authentication** for sensitive
operations. Low-risk actions (read, comment, write) do not require a
recent MFA verification, but sensitive actions (deleteDocument,
adminOperation) require that the principal's MFA challenge was
completed within the last 15 minutes of the current request time.

Principal is `User`; resources are `Document` and `Workspace`. Every
User, Document, and Workspace belongs to a common Workspace scope
(users can only act within their home workspace).

## Requirements

### 1. Workspace Isolation (Baseline)
- A User may act on a Document only when the Document's `workspace`
  matches the User's `workspace`:
  `principal.workspace == resource.workspace`.
- A User may act on a Workspace resource only when it is their own
  workspace: `principal.workspace == resource`.
- This applies to all five actions. Cross-workspace access is never
  permitted.

### 2. Low-Risk Action Access (Permit)
- A User in their own workspace may `read`, `comment`, or `write` any
  Document in that workspace. No MFA freshness check required.
- Specifically: for `read`, `comment`, `write` on a Document, permit
  when `principal.workspace == resource.workspace`.

### 3. Delete Document (MFA-Gated)
- A User may `deleteDocument` on a Document in their workspace ONLY
  when their MFA was verified within the last 15 minutes:
  `context.now.datetime.durationSince(principal.mfaVerifiedAt) <
  duration("15m")`.
- The MFA freshness check is in addition to the workspace isolation
  check.

### 4. Admin Operation (Admin + MFA-Gated)
- A User may `adminOperation` on a Workspace ONLY when ALL of:
  - It is their own workspace: `principal.workspace == resource`, AND
  - They have the admin role: `principal.isAdmin == true`, AND
  - Their MFA was verified within the last 15 minutes:
    `context.now.datetime.durationSince(principal.mfaVerifiedAt) <
    duration("15m")`.
- Non-admin users cannot perform adminOperation under any circumstance,
  regardless of MFA freshness.

## Notes
- Cedar's `datetime.durationSince(other)` method returns the duration
  from `other` to `self`. If `self` is the current request time and
  `other` is the MFA verification time, the result is the elapsed time
  since MFA, which must be less than 15 minutes for sensitive actions.
- The 15-minute window must be expressed as `duration("15m")` — Cedar
  uses Go-style duration strings, not ISO 8601.
- Common failure modes to avoid: (a) forgetting the MFA check on
  delete/admin, (b) using ISO 8601 duration syntax (`PT15M`), (c)
  applying the MFA check to low-risk actions unnecessarily.
