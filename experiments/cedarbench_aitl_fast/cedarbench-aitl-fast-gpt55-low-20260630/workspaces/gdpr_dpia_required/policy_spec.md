---
pattern: GDPR Art. 35 DPIA gating for high-risk processing
difficulty: hard
features:
  - optional datetime attribute (has-guard required)
  - duration arithmetic (durationSince + < duration("365d"))
  - boolean attribute gating
  - per-action policy splits with shared DPIA freshness predicate
  - role-based access with DPO override on terminate
domain: compliance / GDPR
synthesis_difficulty: 4
---

# GDPR Art. 35 DPIA Required — Policy Specification

## Context

GDPR Article 35 requires a Data Protection Impact Assessment (DPIA) to be
performed and approved BEFORE engaging in any "high-risk" processing
activity, and DPIAs go stale and must be refreshed periodically.

Entities:

- `Processor` — a person operating the platform. `role` is one of
  `"controller"` (the data controller) or `"dpo"` (Data Protection Officer).
- `ProcessingActivity` — a registered processing operation, with:
  - `riskLevel` ∈ `{"low", "medium", "high"}`,
  - `dpiaCompletedDate` (optional datetime — present iff a DPIA has been
    completed), and
  - `dpiaApproved` (Bool) — whether the completed DPIA was approved.

Context: `now: datetime` — current wall-clock for staleness checks.

Actions: `initiateProcessing`, `modifyProcessing`, `terminateProcessing`.

A DPIA is "valid" iff it has been completed, was approved, and was
completed within the last 365 days:

```
resource has dpiaCompletedDate
&& resource.dpiaApproved
&& context.now.durationSince(resource.dpiaCompletedDate) < duration("365d")
```

## Requirements

### 1. initiateProcessing
A `Processor` may `initiateProcessing` a `ProcessingActivity` when:
- `principal.role == "controller"`, AND
- Either:
  - `resource.riskLevel` is `"low"` or `"medium"` (no DPIA required), OR
  - `resource.riskLevel == "high"` AND a valid DPIA exists.

### 2. modifyProcessing
Modifying a high-risk processing activity also requires a fresh DPIA
(modifications can change risk profile and re-trigger Art. 35).

A `Processor` may `modifyProcessing` a `ProcessingActivity` when:
- `principal.role == "controller"`, AND
- Either:
  - `resource.riskLevel` is `"low"` or `"medium"`, OR
  - `resource.riskLevel == "high"` AND a valid DPIA exists.

### 3. terminateProcessing
Winding down processing is always allowed for compliance staff,
regardless of DPIA state — you must be able to stop high-risk
processing even if the DPIA has lapsed.

A `Processor` may `terminateProcessing` a `ProcessingActivity` when:
- `principal.role == "controller"` OR `principal.role == "dpo"`.

### 4. Default Deny
All other requests are denied. Notably:

- A controller cannot `initiateProcessing` or `modifyProcessing` a
  high-risk activity if the DPIA is missing, unapproved, or older
  than 365 days.
- A DPO cannot `initiateProcessing` or `modifyProcessing` (only
  controllers run processing; DPO is oversight).
- No role other than controller/DPO can `terminateProcessing`.
