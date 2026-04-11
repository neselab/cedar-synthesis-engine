---
pattern: M2M authorization, scoped bearer tokens
difficulty: medium
features:
  - non-User principal (ApiKey)
  - scope string matching via set membership
  - expiry + revocation forbid composition
  - submitted-invoice read-only override
  - organization-level tenant isolation
domain: API platforms, integrations, third-party SaaS
---

# API Key Scoped Access — Policy Specification

## Context

This policy governs machine-to-machine access via API keys. Unlike
user-facing policies, the principal is an `ApiKey` entity (not a
`User`) — API keys act on behalf of an organization or integration.
Each key has a fixed set of scope strings, an expiry datetime, and a
revocation flag. The policy enforces:

1. **Tenant isolation**: API keys can only act on resources belonging
   to their own organization.
2. **Scope matching**: each action requires a specific scope string to
   be present in the key's `scopes` set.
3. **Expiry**: expired keys reject all requests.
4. **Revocation**: revoked keys reject all requests, regardless of
   expiry state.
5. **Submitted-invoice immutability**: invoices with `submitted == true`
   are read-only even for keys with `write:invoice` scope.

## Requirements

### 1. Baseline Forbid — Expired Keys
- **Forbid** any action on any resource when the key's expiry datetime
  is at or before the current time:
  `context.now.datetime >= principal.expiresAt`. This applies to all
  five actions.

### 2. Baseline Forbid — Revoked Keys
- **Forbid** any action on any resource when the key has been revoked:
  `principal.revoked == true`. This applies to all five actions and
  overrides the expiry check (a key that is both revoked and expired
  is still rejected).

### 3. Organization Isolation
- Permits require that the API key's organization matches the
  resource's organization: `principal.organization ==
  resource.organization`. This is a per-permit condition, not a
  global forbid, to keep the scope-matching logic cleanly expressible.

### 4. Scope-to-Action Mapping
Each action requires a specific scope string in the key's `scopes` set:

| Action           | Required scope string      |
|------------------|----------------------------|
| readDocument     | `"read:document"`          |
| writeDocument    | `"write:document"`         |
| deleteDocument   | `"delete:document"`        |
| readInvoice      | `"read:invoice"`           |
| writeInvoice     | `"write:invoice"`          |

The permit rule for each action checks that the corresponding scope
string is in `principal.scopes`.

### 5. Submitted-Invoice Immutability (Forbid)
- **Forbid** `writeInvoice` when the invoice has been submitted
  (`resource.submitted == true`). Once an invoice is submitted, it
  cannot be modified by any key, even one with `write:invoice` scope.
- Reading submitted invoices is still permitted (the read is not
  blocked).

## Notes
- API keys act as the principal, which means `principal.organization`,
  `principal.scopes`, etc. reference ApiKey attributes — not User
  attributes. This is a novel pattern not tested in any prior
  scenario, where all principals have been `User` or equivalent.
- Scope matching is string set membership: `principal.scopes.contains("read:document")`.
  This is a literal string comparison, not a pattern match.
- The expiry check uses `>=` (key is invalid AT the expiry instant),
  which is one common convention. An alternative is `>` (valid up to
  the expiry instant); the policy uses `>=` per standard bearer-token
  semantics.
- Common failure modes: (a) forgetting the revocation check (only
  checking expiry), (b) missing the submitted-invoice forbid,
  (c) allowing cross-organization access.
