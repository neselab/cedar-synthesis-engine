---
pattern: "twenty-action procurement workflow"
difficulty: hard (scale)
features:
  - 20 distinct workflow actions
  - per-action role gating
  - tests action-set scale
domain: enterprise procurement
synthesis_difficulty: 3
---

# Twenty-Action Workflow — Policy Specification

A procurement workflow with 20 distinct actions covering the full document
lifecycle (request → review → approve → close → archive) plus auxiliary
actions (delegate, escalate, cancel, audit, export, sign, comment).

Each action has specific role gating per the requirements below.

Roles: requester, reviewer, approver, auditor, manager, admin
