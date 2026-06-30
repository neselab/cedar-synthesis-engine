---
pattern: decimal currency with method comparison
difficulty: medium
features:
  - decimal extension
  - method comparison (.lessThan, .greaterThan)
  - precision up to 4 digits
domain: finance / payments
synthesis_difficulty: 3
---

# Decimal Currency Comparison -- Policy Specification

## Context

This policy governs approval of financial transactions at a payments
processor, using Cedar's `decimal` extension to reason about monetary
amounts with fixed-point precision. The system models a classic
tiered-approval workflow: tellers can approve small transactions,
managers can approve mid-sized transactions, and VPs can approve any
transaction. Daily accumulated approvals are tracked to enforce a
per-transaction daily-limit cap. International transactions are
subject to stricter oversight.

Entities:
- `Approver` with `role: String` (one of `"teller"`, `"manager"`, `"vp"`).
- `Transaction` with `amount: decimal`, `dailyLimit: decimal`, and
  `isInternational: Bool`.

Context carries `accumulatedToday: decimal`, representing the sum of
amounts already approved by this approver today. The host application
is responsible for computing this value and passing it in (Cedar's
`decimal` extension supports only comparison, not arithmetic).

Actions: `approve` (initiate an approval), `reverse` (reverse a prior
approval), `audit` (view transaction details).

## Decimal literals (Cedar facts)

Cedar's `decimal` extension represents a fixed-point decimal with up
to 4 fractional digits. Literals are written with a string argument:
`decimal("1000.0000")`. The value must include a period and 1-4
fractional digits. The representable range is approximately
`-922337203685477.5808` to `922337203685477.5807`.

Only method-style comparisons are supported: `.lessThan()`,
`.lessThanOrEqual()`, `.greaterThan()`, `.greaterThanOrEqual()`.
Operator syntax (`<`, `<=`, `>`, `>=`) does NOT work on `decimal`
values and will fail validation. There is also no arithmetic on
`decimal` -- you cannot add, subtract, or multiply decimals.

## Requirements

### 1. Teller Approval Tier (Permit)
- An `Approver` whose `role` is `"teller"` may `approve` a
  `Transaction` whose `amount` is strictly less than `1000.0000`,
  i.e., `resource.amount.lessThan(decimal("1000.0000"))`.

### 2. Manager Approval Tier (Permit)
- An `Approver` whose `role` is `"manager"` may `approve` a
  `Transaction` whose `amount` is strictly less than `50000.0000`,
  i.e., `resource.amount.lessThan(decimal("50000.0000"))`.

### 3. VP Approval -- Any Amount (Permit)
- An `Approver` whose `role` is `"vp"` may `approve` any
  `Transaction` regardless of amount.

### 4. Daily-Limit Cap (applies to teller and manager)
- For tellers and managers, the approver's `context.accumulatedToday`
  must be strictly less than the transaction's `dailyLimit`:
  `context.accumulatedToday.lessThan(resource.dailyLimit)`.
- This is an approximation: because Cedar's `decimal` has no
  arithmetic, we cannot compute `accumulatedToday + amount` inside
  the policy. The host application is responsible for computing the
  precise post-approval accumulated total and enforcing any tighter
  bound. The in-policy check protects against approvals when the
  approver has already hit or exceeded the daily limit.
- VP approvals are exempt from the daily-limit cap.

### 5. International Transactions (applies to teller and manager)
- If `resource.isInternational` is `true`, the transaction's
  `amount` must additionally be strictly less than `10000.0000`,
  i.e., `resource.amount.lessThan(decimal("10000.0000"))`.
- VP approvals are exempt from the international cap.

### 6. Reversal -- VP Only (Permit)
- Only an `Approver` whose `role` is `"vp"` may `reverse` a
  `Transaction`. Tellers and managers may never reverse.

### 7. Audit -- Any Role (Permit)
- Any `Approver` (teller, manager, or vp) may `audit` any
  `Transaction`. There are no amount, role-tier, or daily-limit
  restrictions on audit.

## Notes
- The role values are exactly `"teller"`, `"manager"`, and `"vp"`.
  No other roles exist.
- `decimal` literals MUST include fractional digits (e.g.,
  `decimal("1000.0000")`, not `decimal("1000")`).
- Cedar denies by default, so the absence of a permit is sufficient
  to deny (e.g., a teller approving a $5000 transaction is not
  matched by any permit, so it is denied).
