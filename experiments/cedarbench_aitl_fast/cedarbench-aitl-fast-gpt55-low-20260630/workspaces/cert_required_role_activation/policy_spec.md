---
pattern: certificate-gated role activation — short-lived signed credential elevates privileges
difficulty: medium
features:
  - optional record-typed context attribute (`cert?: { ... }`)
  - triple has-guard chain on optional record fields (§8.3)
  - datetime comparison against issued credential expiry
  - signer trust check (string equality on certificate authority)
  - role activation via either base entitlement OR cert claim
domain: workforce identity / short-lived credentials / PKI
synthesis_difficulty: 3
---

# Certificate-Required Role Activation — Policy Specification

## Context

This policy implements **certificate-gated role activation** for
privileged operations. Operators have a baked-in `baseRole` attribute
representing their long-lived role assignment. For some operations a
non-admin operator may **temporarily activate** the admin role by
presenting a short-lived signed certificate whose claim matches the
required role. The certificate must be unexpired and signed by a
trusted certificate authority.

Principal is `Operator`; resource is `Resource`. Two actions are
defined: `view` (any operator) and `executeAdmin` (requires admin
entitlement, either via base role or via a valid certificate claim).

## Requirements

### 1. View Access (Permit)

- Any `Operator` whose `baseRole` is `"user"` or `"admin"` may
  perform `view` on any `Resource`. No certificate is required.
- The view action does not gate on a certificate at all — even if a
  cert is supplied, it is not consulted for `view`.

### 2. Execute Admin (Permit)

An `Operator` may perform `executeAdmin` on a `Resource` if **either**
condition (a) or condition (b) holds:

**(a) Base admin entitlement.** The operator's baked-in role is
admin: `principal.baseRole == "admin"`. No certificate needed.

**(b) Certificate-elevated admin.** All four conditions hold:
  - A `cert` record is present in the request context
    (`context has cert`),
  - The certificate is unexpired:
    `context.cert.validUntil > context.now`,
  - The certificate's claimed role is admin:
    `context.cert.claimedRole == "admin"`,
  - The certificate is signed by the trusted certificate authority:
    `context.cert.signer == "trusted-ca"`.

A cert with `claimedRole == "admin"` but signed by some other party,
or one that has expired, MUST NOT activate the admin role. A cert
that claims a non-admin role (e.g. `"user"`) MUST NOT activate admin
either.

### 3. Default Deny

- An operator with `baseRole == "user"` and no certificate (or with
  an invalid certificate) MUST be denied `executeAdmin`.
- An operator with `baseRole == "guest"` is denied both `view` and
  `executeAdmin` regardless of any certificate.

## Notes

- The `cert` attribute is declared optional in the schema (`cert?`),
  so EVERY read of `context.cert.<field>` must be preceded by a
  `context has cert` guard in the same conjunction (§8.3 negated-has
  trap). Three certificate-field reads → three has-guard occurrences,
  one per conjunct (Cedar's typechecker does not propagate the guard
  across `&&` chains for negated conditions, and the safest pattern
  is to inline the guard at each use).
- `now` is required and lives at `context.now` as a top-level
  `datetime`. Comparisons use `>` / `<` / `<=` / `>=` directly on
  `datetime` values.
- Common failure modes to avoid: (a) reading `context.cert.signer`
  without a `context has cert` guard (validation error), (b) accepting
  any signer rather than `"trusted-ca"` only, (c) accepting a
  `claimedRole` value other than `"admin"`, (d) gating `view` on the
  certificate by mistake.
