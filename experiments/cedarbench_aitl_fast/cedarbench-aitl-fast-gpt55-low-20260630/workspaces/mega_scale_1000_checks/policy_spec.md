---
pattern: "mega scale RBAC matrix (1000-check stress test)"
difficulty: hard (scale)
features:
  - 50 roles × 20 actions = 1000-cell RBAC matrix
  - 1040 total verification checks
  - 2x scale of mega_scale_500_checks
  - tests harness ceiling for plan size and feedback formatting
domain: e-commerce back-office (meta / harness stress)
synthesis_difficulty: 3
---

# Mega-Scale 1000-Check Stress — Policy Specification

A doubly-scaled version of mega_scale_500_checks. 50 roles, 20 actions,
all permitted (correct policy is essentially `permit when role in [50 strings]`).
The point is operational scale, not policy complexity. Tests whether the
harness can process 1040 verification checks per iteration without
degrading on conversation trimming, feedback size, or symcc invocation.
