---
pattern: "fifty-role × 10-action RBAC matrix"
difficulty: hard (scale)
features:
  - 50 roles × 10 actions = 500-cell matrix
  - all-permit baseline (correct policy: permit when role in 50 strings)
  - smaller than mega_scale_500 in cells but larger role count
domain: enterprise RBAC at scale
synthesis_difficulty: 3
---

# Fifty-Role Matrix — Policy Specification

50 distinct roles × 10 actions. Tests harness handling of large role
namespaces. All roles can do all actions; correct policy is broad permit.
