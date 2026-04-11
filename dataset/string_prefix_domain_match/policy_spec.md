---
pattern: email-based ACL / string pattern matching
difficulty: medium
features:
  - string prefix matching (email local-part)
  - string suffix matching (email domain)
  - subdomain disambiguation
domain: any SaaS with email-based identity
---

# Email-Based Domain Access Control — Policy Specification

## Context

This policy implements email-based access control. Access is determined
by pattern-matching the principal's email address against fixed string
patterns.

Principal is `User` with an `email: String` attribute. Resource is
`Resource` with a `classification: String` attribute (one of `"public"`,
`"internal"`, `"partner"`). Two actions: `readResource`, `writeResource`.

## Requirements

### 1. Public Read (All Users)
- Any User may `readResource` when the resource's classification is
  `"public"`, regardless of their email.

### 2. Internal Read (Employee Domain)
- A User whose email **ends with** `@example.com` may `readResource`
  when the resource's classification is `"internal"`. For example,
  `alice@example.com` qualifies; `bob@other.com` does not.

### 3. Partner Read (Partner Subdomain)
- A User whose email **ends with** `@partner.example.com` may
  `readResource` when the resource's classification is `"partner"`.
  Note that `@partner.example.com` is a more specific pattern than
  `@example.com` — every `@partner.example.com` address also ends
  with `@example.com`, so partner users automatically qualify for
  the employee rule above as well.

### 4. Admin Write (Admin Local-Part)
- A User whose email **starts with** `admin@` may `writeResource` on
  any resource, regardless of classification. For example,
  `admin@example.com`, `admin@partner.example.com`, and
  `admin@other.org` all qualify.

## Notes
- Cedar has one string-matching primitive. Refer to the Cedar
  documentation for the exact syntax.
- The "ends with" and "starts with" semantics are the standard ones:
  "ends with X" means the last N characters of the string are exactly
  X, where N is the length of X.
- Common pitfalls in policy implementation: reaching for methods that
  do not exist in Cedar, or confusing the wildcard conventions of
  different pattern-matching systems (e.g., regex `.*` vs glob `*`).
