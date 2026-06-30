---
pattern: loan approval workflow
difficulty: hard
features:
  - numeric comparison (approvalLimit >= amount)
  - role-string gating
  - risk-based escalation
  - state-machine guard (isSubmitted)
  - multi-condition conjunction
domain: banking/finance
synthesis_difficulty: 3
---

# Loan Approval Workflow — Policy Specification

## Context

This policy governs a multi-tier banking loan approval system. An
`Officer` handles `LoanApplication` resources through a lifecycle of
submission, review, approval/rejection, and escalation. Approval
authority is determined by the officer's approval limit and the loan's
risk rating.

Principal is `Officer`; resource is `LoanApplication`. There are five
actions: `submit`, `review`, `approve`, `reject`, `escalate`.

## Entity Model

- **Officer**: the principal. Each Officer has:
  - `role: String` — one of `"analyst"`, `"manager"`, `"director"`,
    `"vp"`. Determines which actions are available and whether the
    officer can approve high-risk loans.
  - `approvalLimit: Long` — the maximum loan amount this officer is
    authorized to approve. The officer may approve loans with
    `amount <= approvalLimit`.

- **LoanApplication**: the resource. Each LoanApplication has:
  - `amount: Long` — the requested loan amount in dollars.
  - `riskRating: String` — one of `"low"`, `"medium"`, `"high"`.
    High-risk loans require director-or-above approval regardless of
    the officer's limit.
  - `isSubmitted: Bool` — whether the application has been submitted
    for review. Actions other than `submit` generally require the
    application to be submitted.

## Requirements

### 1. Submit (Analyst Only, Not Yet Submitted)
- Only officers with `role == "analyst"` may submit a loan application.
- The application must NOT already be submitted: `!resource.isSubmitted`.
- Concretely: permit `submit` when `principal.role == "analyst"` AND
  `!resource.isSubmitted`.
- No other role may submit, even if they meet other conditions.

### 2. Review (Any Officer, Submitted)
- Any officer may review a loan application that has been submitted.
- Concretely: permit `review` when `resource.isSubmitted`.
- There are no role or limit restrictions on review; it is purely
  informational.

### 3. Approve (Limit + Risk Check, Submitted)
- An officer may approve a loan application when ALL of:
  - The application is submitted: `resource.isSubmitted`.
  - The officer's approval limit is sufficient:
    `principal.approvalLimit >= resource.amount`.
  - For high-risk loans (`resource.riskRating == "high"`), the officer
    must be a director or VP: `principal.role == "director"` or
    `principal.role == "vp"`.
- Low-risk and medium-risk loans have no additional role constraint
  beyond the limit check.
- Concretely: permit `approve` when `resource.isSubmitted` AND
  `principal.approvalLimit >= resource.amount` AND
  `(resource.riskRating != "high" || principal.role == "director" || principal.role == "vp")`.

### 4. Reject (Any Officer, Submitted)
- Any officer may reject a submitted loan application.
- Concretely: permit `reject` when `resource.isSubmitted`.
- There are no role or limit restrictions on rejection.

### 5. Escalate (Any Officer, Submitted)
- Any officer may escalate a submitted loan application to a higher
  authority for further review.
- Concretely: permit `escalate` when `resource.isSubmitted`.
- This action is used when an officer's limit is insufficient or
  when additional review is warranted.

## Notes
- The `approvalLimit >= amount` check is the core authorization
  property for approval. A candidate that omits this check allows
  officers to approve loans beyond their authority.
- The high-risk escalation rule (`riskRating == "high"` requires
  director or VP) is an additional gate that compounds with the limit
  check. Both conditions must hold simultaneously.
- Cedar denies by default; only the five permits above are needed.
  There are no explicit forbid rules in this scenario.
- The `isSubmitted` guard on most actions prevents premature
  review/approval/rejection/escalation of draft applications.
