---
pattern: data lineage ancestry
difficulty: hard
features:
  - hierarchical string-enum clearance (public < internal < restricted)
  - boolean attribute gate (hasPersonalData)
  - department-scoped actions (derive, delete)
  - four distinct actions with layered requirements
domain: data engineering
synthesis_difficulty: 3
---

# Data Lineage Ancestry -- Access Inherits from Data Labels

## Context

A data-engineering platform manages datasets that flow through ETL
pipelines. Each dataset carries a classification label inherited from
its upstream lineage: `public`, `internal`, or `restricted`. Users have
a clearance string at the same three levels. Access to a dataset
depends on the user's clearance relative to the dataset's
classification, and some actions impose additional constraints based on
the dataset's source department or whether it contains personal data.

## Requirements

### Action: query

A user may query a dataset when their clearance is sufficient for the
dataset's classification level. The hierarchy is:

- `public` datasets: any clearance (`public`, `internal`, `restricted`).
- `internal` datasets: clearance `internal` or `restricted`.
- `restricted` datasets: clearance `restricted` only.

### Action: derive (create a derived dataset)

A user may derive from a dataset when ALL of the following hold:

1. The user's clearance is sufficient for the dataset's classification
   (same hierarchy as query).
2. The user's department matches the dataset's source department.

### Action: export

A user may export a dataset when ALL of the following hold:

1. The user's clearance is sufficient for the dataset's classification
   (same hierarchy as query).
2. The dataset does NOT contain personal data
   (`resource.hasPersonalData == false`).

### Action: delete

A user may delete a dataset when ALL of the following hold:

1. The user's clearance is `restricted` (highest tier only).
2. The user's department matches the dataset's source department.

### Liveness

Each of the four actions must permit at least one request.

## Out of scope

- No temporal constraints.
- No role-based groups or team membership beyond the clearance string.
- No global forbids -- all restrictions are encoded as conditions on permits.
