---
pattern: GDPR Art. 5.1.b purpose limitation
difficulty: medium
features:
  - set membership for purpose tags (allowedPurposes.contains)
  - optional context attribute with has-guard (compatible-use exception)
  - per-action role gating (controller / processor / dpo)
  - boolean consent gate
domain: privacy, compliance, EU data protection
synthesis_difficulty: 3
---

# GDPR Purpose Limitation — Policy Specification

## Context

This policy implements GDPR Article 5.1.b ("purpose limitation"): personal
data collected for one specified, explicit, and legitimate purpose may not
be further processed in a manner incompatible with that purpose. Each
`PersonalData` record carries the set of purposes its data subject
consented to (`allowedPurposes`) and a top-level consent flag
(`subjectConsent`). At access time, the requesting context must declare
the purpose for which the data is being accessed (`context.declaredPurpose`),
and that purpose must either appear in the data record's `allowedPurposes`
set OR a "compatible use" approval must be attached to the request
(`context.compatibleUseApproval == true`) — the latter is GDPR's narrow
escape hatch for further processing under Art. 6.4.

Three actions are gated by this policy:
- `read`: any role may read.
- `process`: only `controller` and `processor` roles may process.
- `disclose`: only the `dpo` (data protection officer) may disclose.

All three actions require both consent and purpose-match (or compatible-use
approval).

## Entities

### `Processor`
- `role: String` — one of `"controller"`, `"processor"`, `"dpo"`.

### `PersonalData`
- `allowedPurposes: Set<String>` — purpose tags for which the data subject
  has given consent (e.g. `{"analytics", "marketing"}`).
- `subjectConsent: Bool` — top-level consent flag. If `false`, no access is
  permitted under any circumstance, even with a compatible-use approval.

### Context
- `declaredPurpose: String` — the purpose the requester is invoking
  (e.g. `"billing"`).
- `compatibleUseApproval?: Bool` — OPTIONAL. When present and `true`, this
  is the host application's signed assertion that a compatible-use review
  has been performed under Art. 6.4 and the cross-purpose access is
  permitted. The flag is OPTIONAL because most requests do not need it;
  policies MUST `has`-guard before reading.

## Requirements

### 1. Read access
A `Processor` may `read` a `PersonalData` record when ALL of:
- `resource.subjectConsent == true`, AND
- (`resource.allowedPurposes.contains(context.declaredPurpose)` OR
   the request carries `context.compatibleUseApproval == true`).

Any role (controller, processor, dpo) may read when these conditions hold.

### 2. Process access
A `Processor` may `process` a `PersonalData` record when ALL of:
- the read conditions above hold, AND
- `principal.role == "controller"` OR `principal.role == "processor"`.

The DPO is NOT permitted to process; the DPO is an oversight role, not an
operational role.

### 3. Disclose access
A `Processor` may `disclose` a `PersonalData` record when ALL of:
- the read conditions above hold, AND
- `principal.role == "dpo"`.

Only the DPO may disclose. Controllers and processors may not disclose
directly — disclosure decisions are routed through the DPO.

### 4. Negative requirements
- Without `subjectConsent == true`, no access (read, process, or disclose)
  is permitted under any circumstance, including with `compatibleUseApproval`.
  Consent is the gate; compatible-use is only relief from purpose-match.
- Without purpose-match AND without compatible-use approval, no access is
  permitted.

## Notes
- `compatibleUseApproval` is OPTIONAL in the context schema (declared with
  `?`). Reading it without a `has`-guard is a Cedar type error. The
  correct guard pattern is
  `(context has compatibleUseApproval && context.compatibleUseApproval)`.
- Naively writing `!(context has compatibleUseApproval) ||
  context.compatibleUseApproval` triggers the §8.3 negated-`has` trap and
  is rejected by Cedar's type-checker. Use the positive form.
- The purpose-match check is a direct set-membership: 
  `resource.allowedPurposes.contains(context.declaredPurpose)`.
- Common failure modes: (a) treating compatible-use as a consent override,
  (b) letting the DPO process or letting controllers disclose,
  (c) forgetting to has-guard the optional flag, (d) splitting the policy
  by role rather than by action and losing the per-action role gate.
