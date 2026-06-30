---
pattern: "five-namespace cross-reference"
difficulty: hard (scale)
features:
  - 5 top-level namespaces
  - cross-namespace entity type references
  - qualified entity names throughout policies
domain: enterprise multi-domain platform
synthesis_difficulty: 3
---

# Five-Namespace Coordination — Policy Specification

Five distinct top-level namespaces, each with entities referencing entities
in other namespaces. Tests Cedar's qualified-name handling at scale.

Namespaces: Identity, Billing, Catalog, Shipping, Audit
