---
pattern: "mega scale RBAC matrix (500-check stress test)"
difficulty: hard (scale)
features:
  - 25 roles × 20 actions = 500-cell RBAC matrix
  - 540 total verification checks
  - tests harness conversation trimming at scale
  - tests verification plan handling beyond 157 (prior max)
domain: e-commerce back-office (meta / harness stress)
synthesis_difficulty: 3
---

# Mega-Scale 500-Check Stress — Policy Specification

## Context

A large e-commerce back-office RBAC system with 25 distinct roles
and 20 distinct actions on `Order` resources, producing a 500-cell
permission matrix. This scenario is the harness's primary scale
stress test — at over 3× the prior maximum (157 checks in
`hundred_check_scale`), it pushes the conversation-trimming heuristic,
per-iteration feedback formatting, hash-based oscillation tracking,
and verification orchestration to their limits.

The correct policy is **structurally simple** but the verification
plan is **operationally large**. The scale stresses the harness, not
the synthesizer's reasoning.

## Roles

The 25 roles cover the full operational surface of an e-commerce
platform: customer service tiers (viewer, cs_agent, cs_senior,
cs_manager, cs_director), fulfillment chain (fulfillment_basic,
fulfillment_lead, fulfillment_manager, warehouse), returns (returns_agent,
returns_lead), finance (finance_basic, finance_senior, finance_manager,
finance_director), risk (risk_analyst, risk_manager), pricing
(pricing_analyst, pricing_manager), platform (platform_ops,
platform_admin), security (security_basic, security_admin), and
audit/compliance (audit_read, compliance_officer).

## Actions

The 20 actions span CRUD plus domain-specific operations:
viewOrder, listOrders, createOrder, updateOrder, cancelOrder,
refundOrder, partialRefund, shipOrder, markDelivered, returnOrder,
disputeOrder, resolveDispute, viewPII, maskPII, exportData,
bulkOperations, modifyPricing, applyDiscount, voidTransaction,
adminOverride.

## Requirements

### Permission matrix
For the purpose of this stress test, EVERY role is permitted to
perform EVERY action on every Order. The correct policy is therefore
essentially `permit (principal is User, action, resource is Order);`
or equivalently a permit gated by the role being any of the 25
declared roles.

### Default deny
Any principal whose `role` attribute is not one of the 25 declared
roles is denied all actions. This is the only restriction.

### Why all-permitted
The point of this scenario is **harness scale**, not policy
complexity. The harness must:
- Load and process 540 verification checks
- Format 540 per-check results into LLM feedback
- Maintain hash-based oscillation tracking across iterations with
  large feedback payloads
- Avoid context window exhaustion via conversation trimming
- Complete in reasonable time (target: <5 minutes per iteration)
