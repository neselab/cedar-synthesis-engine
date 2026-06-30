---
pattern: PCI DSS scope reduction via tokenization, CDE boundary enforcement
difficulty: medium
features:
  - non-User principal (System)
  - data-classification gating (PAN vs TOKEN vs MASKED_PAN)
  - cardholder data environment (CDE) membership check
  - dual-attribute requirement (cdeAuthorized AND auditCompliant)
  - data-type-conditional audit restrictions
domain: payments, fintech, PCI compliance
synthesis_difficulty: 3
---

# PCI DSS CDE Boundary — Policy Specification

## Context

Under PCI DSS, the Cardholder Data Environment (CDE) is the set of
systems that store, process, or transmit Primary Account Number (PAN)
data. Tokenization is the primary mechanism for reducing PCI scope:
most systems should never see raw PAN — they only ever see tokens or
masked PAN. This policy enforces the CDE boundary across four actions:
`read`, `tokenize`, `detokenize`, and `audit` over `PaymentRecord`
resources.

The principal type is `System` (a service or process), not a user.
Each system carries two compliance flags: `cdeAuthorized` (the system
is in scope and approved to handle PAN) and `auditCompliant` (the
system passes a stronger audit-trail requirement, needed for
detokenization specifically).

## Requirements

### 1. read action — gated by data type

- If `resource.dataType == "PAN"`: permit only when
  `principal.cdeAuthorized && resource.cdeMember`.
- If `resource.dataType == "TOKEN"`: permit any system (tokens are
  not sensitive — that is the whole point of tokenization).
- If `resource.dataType == "MASKED_PAN"`: permit any system (masked
  data is safe to expose broadly).

### 2. tokenize action

- Always requires `principal.cdeAuthorized`. Tokenization takes a PAN
  as input, so the system must be CDE-authorized to invoke it.
- The resource being tokenized must currently be a PAN
  (`resource.dataType == "PAN"`). Tokenizing a token or a masked PAN
  is meaningless.

### 3. detokenize action — highest restriction

- Requires BOTH `principal.cdeAuthorized` AND `principal.auditCompliant`.
  Detokenization re-exposes raw PAN, so it carries the strongest
  prerequisites in the policy.
- The resource must be a `TOKEN` (`resource.dataType == "TOKEN"`).

### 4. audit action

- Any system can audit a `PaymentRecord`, **except** when the record
  contains raw PAN: in that case `principal.cdeAuthorized` is also
  required. (Auditing PAN exposes PAN to the auditor, so the auditor
  must be CDE-authorized.)
- For `dataType` of `TOKEN` or `MASKED_PAN`, no extra restriction —
  any system can audit.

## Notes

- The `cdeMember` attribute on the resource records whether the
  *record itself* lives inside the CDE. Reading PAN requires both
  the principal to be cdeAuthorized AND the record to be cdeMember:
  a misclassified record outside the CDE must still be locked down,
  and an out-of-CDE principal must be unable to reach in.
- Common failure modes:
  (a) treating `cdeAuthorized` alone as sufficient for PAN read
      without checking `cdeMember`,
  (b) forgetting that `auditCompliant` is required *in addition to*
      `cdeAuthorized` for detokenize,
  (c) allowing audit of PAN without cdeAuthorized.
- Per **§8.8 floor-bound consistency**, every floor that asserts a
  PAN-touching action must include the CDE check (cdeAuthorized for
  the principal, and where applicable cdeMember on the resource).
  Floors that omit this would be jointly unsatisfiable with the
  ceiling.
