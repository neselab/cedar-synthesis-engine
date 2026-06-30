---
pattern: large-scale RBAC matrix (harness scale stress test)
difficulty: hard (scale, not semantics)
features:
  - 10-role × 10-action permission matrix
  - Per-action status constraints (cart / pending / shipped / delivered / refunded)
  - ~157 verification checks (3-5x larger than any prior scenario)
domain: e-commerce back-office, meta-harness test
synthesis_difficulty: 3
---

# Hundred-Check Scale — E-Commerce Back-Office Policy

## Context

This policy governs access control for an e-commerce back-office
platform with ten job roles and ten order-management actions. Each
(role, action) pair is permitted or denied by a matrix derived from
business ownership. Some actions also have order-status constraints
(e.g., you can only ship a pending order, only refund a delivered
order).

Principal is `User` with a `role: String` attribute. Resource is
`Order` with `status: String` and `total: Long`. Ten actions:
`viewOrder`, `listOrders`, `updateCart`, `placeOrder`, `cancelOrder`,
`refundOrder`, `shipOrder`, `markDelivered`, `modifyPricing`,
`adminOverride`.

## Role / Action Matrix

| Role              | view | list | updateCart | placeOrder | cancel | refund | ship | delivered | pricing | override |
|-------------------|:----:|:----:|:----------:|:----------:|:------:|:------:|:----:|:---------:|:-------:|:--------:|
| viewer            | ✓    | ✓    | ✓          | ✓          |        |        |      |           |         |          |
| cs_agent          | ✓    | ✓    | ✓          | ✓          | ✓      |        |      |           |         |          |
| cs_manager        | ✓    | ✓    | ✓          | ✓          | ✓      | ✓      |      |           |         |          |
| fulfillment       | ✓    | ✓    |            |            |        |        | ✓    | ✓         |         |          |
| warehouse_lead    | ✓    | ✓    |            |            |        |        | ✓    | ✓         |         |          |
| returns           | ✓    | ✓    |            |            |        |        |      |           |         |          |
| finance_ops       | ✓    | ✓    |            |            | ✓      | ✓      |      |           |         |          |
| finance_manager   | ✓    | ✓    |            |            | ✓      | ✓      |      |           | ✓       |          |
| platform_admin    | ✓    | ✓    |            |            |        |        |      |           | ✓       | ✓        |
| security_admin    | ✓    | ✓    |            |            |        |        |      |           |         | ✓        |

## Status Constraints

Some actions are only meaningful in certain order states:

- **updateCart**: requires `status == "cart"`.
- **placeOrder**: transitions cart → pending; requires `status == "pending"` (the policy is checked post-transition).
- **cancelOrder**: requires `status == "pending"`.
- **refundOrder**: requires `status == "delivered"`.
- **shipOrder**: requires `status == "pending"`.
- **markDelivered**: requires `status == "shipped"`.
- **viewOrder**, **listOrders**: any status.
- **modifyPricing**, **adminOverride**: any status.

## Requirements

For each (role, action) pair marked ✓ in the matrix, the policy must
permit the action for that role, subject to the status constraint.
For unmarked pairs, Cedar's default-deny suffices — no explicit
forbid is required.

The policy must refuse all cross-matrix access: e.g., a `viewer`
cannot `refundOrder` under any circumstance, regardless of order
status or any other attribute.

## Notes
- This is primarily a **scale test** for the harness. The policy
  semantics are mechanical (a 10x10 permission matrix), but the
  resulting verification plan has ~157 checks — roughly 3-5x the
  size of any prior scenario. The test hunts for issues in:
  - Conversation trimming (keeps first message + last 8 turns; may
    miss crucial feedback for large plans)
  - Feedback message length (the check list + counterexamples may
    exceed a reasonable context budget)
  - Hash-based oscillation detection (more checks means more unique
    candidate hashes)
  - Phase 2 iteration cost (each iteration triggers 157 symcc calls,
    which compounds wall-clock time)
- The policy itself is expressible in Cedar without any novel
  features — just string equality comparisons on role and status.
  The challenge for Haiku is composing 10+ permit rules correctly,
  each with its own condition, without cross-contamination.
