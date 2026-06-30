---
pattern: long arithmetic overflow avoidance (budget tracking)
difficulty: hard
features:
  - Cedar Long arithmetic (+, -, *)
  - overflow-safe encoding
  - role-gated approval
  - context-provided amounts
domain: financial / project budgeting
synthesis_difficulty: 4
---

# Long Arithmetic Overflow Avoidance — Policy Specification

## Context

A project budgeting system where `Approver` principals submit and approve
spend requests against a `Project` budget. Cedar's `Long` type is a signed
64-bit integer with range `[-9223372036854775808, 9223372036854775807]`.
Cedar provides `+`, `-`, and `*` (no division) on `Long`. There is **no
overflow detection at validation time** — overflow at runtime causes the
policy evaluation to error, and an erroring policy is **ignored**. This
means a `permit` whose `when` clause overflows fails to permit (effective
deny), which can silently break access in production at extreme values.

This scenario tests the planner's ability to write **overflow-safe
arithmetic encodings** rather than the naive form.

## Entities

- `Project` with attributes:
  - `spentSoFar: Long` — money already committed
  - `monthlyBudget: Long` — the cap
- `Approver` with attribute:
  - `role: String` — `"member"` | `"admin"`

## Context

- `requestedAmount: Long` — the dollars in this request
- `now: datetime` — request time (informational; not load-bearing)

## Actions

- `requestSpend` — submit a spend request
- `approveSpend` — approve a spend request (admin-gated)

## Requirements

### 1. Naive (FORBIDDEN) encoding

The naive form
```
permit when resource.spentSoFar + context.requestedAmount <= resource.monthlyBudget
```
can overflow if `spentSoFar + requestedAmount` exceeds `Long::MAX` even
when `monthlyBudget` is small. On overflow the policy errors and is
ignored, silently denying valid requests.

### 2. Safe encoding (REQUIRED)

Rewrite the budget check so the intermediate computation cannot overflow:
```
context.requestedAmount <= resource.monthlyBudget - resource.spentSoFar
```
This is safe when `spentSoFar <= monthlyBudget` (which the host enforces).
The combined safe form also includes a guard:
```
resource.spentSoFar < resource.monthlyBudget
&& context.requestedAmount > 0
&& context.requestedAmount <= resource.monthlyBudget - resource.spentSoFar
```

### 3. requestSpend
Any `Approver` may `requestSpend` on a `Project` when:
- `context.requestedAmount > 0`
- The project still has budget headroom: `resource.spentSoFar < resource.monthlyBudget`
- The request fits using the **safe** form:
  `context.requestedAmount <= resource.monthlyBudget - resource.spentSoFar`

### 4. approveSpend
Only admin approvers may `approveSpend`, with the same numeric guards:
- `principal.role == "admin"`
- `context.requestedAmount > 0`
- `resource.spentSoFar < resource.monthlyBudget`
- `context.requestedAmount <= resource.monthlyBudget - resource.spentSoFar`

### 5. Default Deny
All other requests are denied.
