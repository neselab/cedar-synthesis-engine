---
pattern: "ten-level entity in chain (transitive membership at depth 10)"
difficulty: hard (scale)
features:
  - 10-level deep entity hierarchy
  - transitive `in` across all levels
  - tests symcc handling of deep `in` reasoning
domain: enterprise organizational hierarchy
synthesis_difficulty: 3
---

# Ten-Level Hierarchy — Policy Specification

A ten-level organizational hierarchy:
Org → Co → Region → Division → Dept → Team → Squad → Group → Pair → Individual

The principal `Individual` is transitively `in` all 9 ancestor levels via
Cedar's `in` operator. The policy uses `principal in resource.parentOrg`
where `parentOrg: Org` to verify the principal is anywhere in the chain.

Tests symcc's ability to reason about deep `in` chains. Per §8.10 we know
liveness with entity-graph `in` is unprovable; this scenario uses the
attribute-based `parentOrg` reference + literal Org entity equality
to keep liveness verifiable.
