---
pattern: high-precision financial calculations using Cedar decimal extension
difficulty: hard
features:
  - decimal extension
  - method-style comparison
  - precision boundaries
  - financial threshold enforcement
domain: finance / banking
synthesis_difficulty: 3
---

# Decimal Precision Boundary -- Policy Specification

## Context

This policy governs financial operations on `Account` resources where
both the account state (`balance`, `creditLimit`) and the transaction
parameters (`amount`, `feeRate`) are stored as Cedar `decimal` values.
Cedar's `decimal` extension is purpose-built for representing exact
financial quantities without binary floating-point error, so it is the
correct type for any threshold comparison that must be enforced
faithfully (e.g. "balance is strictly positive," "amount is at most one
million dollars").

The wrinkle: Cedar's `decimal` type does NOT support arithmetic
operators. There is no `+`, `-`, `*`, `/` on decimal values. There is
also no overloading of the standard comparison operators `<`, `>`,
`<=`, `>=` for decimal -- those are only defined for `Long`. The only
way to compare two decimals is to call one of four METHODS on a decimal
value:

  - `.lessThan(other)`
  - `.lessThanOrEqual(other)`
  - `.greaterThan(other)`
  - `.greaterThanOrEqual(other)`

Decimal literals are constructed via `decimal("...")` where the string
must contain a `.` and have between 1 and 4 fractional digits. The
overall representable range is
`-922337203685477.5808 .. 922337203685477.5807` (signed 64-bit fixed
point with a 4-digit fractional part). Constructing a decimal outside
that range, or with a malformed string, is a runtime error -- so the
policy author must keep all literals well inside the boundary.

Entities: `Account` (with `balance: decimal` and `creditLimit: decimal`),
`Transaction` (with `amount: decimal` and `feeRate: decimal`).

Actions:
  - `withdraw` -- principal: User, resource: Account
  - `transfer` -- principal: User, resource: Transaction
  - `viewBalance` -- principal: User, resource: Account

Each action's resource is the correct entity type for the rule it
enforces (an Account for balance-driven gates, a Transaction for
amount-driven gates).

## Requirements

### 1. withdraw (Permit)
- A User may `withdraw` from an Account ONLY IF the account holds a
  strictly positive balance, expressed as
  `resource.balance.greaterThan(decimal("0.0001"))`. The choice of
  `0.0001` (the smallest representable positive decimal at 4-digit
  precision) makes "strictly positive" expressible as a single
  threshold comparison without arithmetic.

### 2. transfer (Permit)
- A User may execute a `transfer` Transaction ONLY IF BOTH:
  - `resource.amount.greaterThan(decimal("0.0000"))` (positive
    transfer amount), AND
  - `resource.amount.lessThanOrEqual(decimal("1000000.0000"))`
    (transfer amount at most one million).

### 3. viewBalance (Permit)
- Any User may `viewBalance` on any Account. The balance display is
  not gated by any decimal threshold -- this rule exists to exercise
  the third action without introducing a fourth threshold value.

## Notes

- Cedar denies by default, so the absence of a permit for a
  zero-balance withdrawal, an out-of-range transfer, etc., is
  sufficient. No explicit `forbid` is required.
- Comparisons MUST use the method form. Writing `resource.balance > 0`
  or `resource.amount <= 1000000` is rejected by `cedar validate` --
  the validator does not allow `<`, `>`, `<=`, `>=` on `decimal`.
- Decimal literals MUST be string-constructed with `decimal("...")`
  and MUST contain a `.` with 1 to 4 fractional digits. `decimal("100")`
  is rejected; `decimal("100.0000")` is accepted.
- All thresholds in this policy (`0.0001`, `0.0000`, `1000000.0000`)
  sit comfortably inside the representable decimal range and so do not
  trigger range-overflow runtime errors during symbolic analysis.
- The policy intentionally does NOT compute fees or net-of-fee
  balances, because Cedar `decimal` cannot do arithmetic. Fee rates
  appear in the schema purely as data the host application would
  apply outside the policy decision.
