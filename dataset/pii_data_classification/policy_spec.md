---
pattern: MLS / compartmentalization / need-to-know
difficulty: medium
features:
  - string-enum hierarchy (clearance vs classification)
  - compositional forbids (PII training, need-to-know)
  - action variants (read vs download with different requirements)
domain: government, healthcare, defense
---

# PII Data Classification — Policy Specification

## Context

This policy implements a classic Multi-Level Security (MLS) pattern
with hierarchical data classification and user clearance. Every
Document has a `classification` label (one of `"Public"`, `"Internal"`,
`"Confidential"`, `"Restricted"`), and every User has a `clearance`
tier (one of `"L1"`, `"L2"`, `"L3"`, `"L4"`). Access requires that
the user's clearance *dominates* the data's classification.

Three additional rules layer on top of the clearance/classification
check:
1. **PII gate**: documents with `containsPII == true` also require
   the user to have completed PII training.
2. **Need-to-know**: "Restricted" documents require the user to be
   explicitly listed in the document's `needToKnow` set, on top of
   the clearance check.
3. **Download scrutiny**: the `downloadDocument` action is stricter
   than `readDocument` — downloading requires a clearance *strictly
   greater* than the data's classification level, not merely equal.

Principal is `User`; resource is `Document`. Two actions: `readDocument`
and `downloadDocument`.

## Clearance / Classification Hierarchy

The ordering is `L1 < L2 < L3 < L4` for clearance and `Public <
Internal < Confidential < Restricted` for classification. The access
mapping for `readDocument` is:

| Classification | Required clearance for read |
|----------------|------------------------------|
| Public         | L1 or higher                 |
| Internal       | L2 or higher                 |
| Confidential   | L3 or higher                 |
| Restricted     | L4 only                      |

For `downloadDocument`, the required clearance is one level *higher*
than for reading:

| Classification | Required clearance for download |
|----------------|----------------------------------|
| Public         | L2 or higher                     |
| Internal       | L3 or higher                     |
| Confidential   | L4 only                          |
| Restricted     | (impossible — no clearance above L4) |

Thus **Restricted documents can never be downloaded** under any
circumstance; they can only be read in place.

## Requirements

### 1. Read Access (Baseline)
A User may `readDocument` when their clearance dominates the document's
classification per the read table above:
- `classification == "Public"`: any clearance (L1, L2, L3, L4).
- `classification == "Internal"`: L2, L3, or L4.
- `classification == "Confidential"`: L3 or L4.
- `classification == "Restricted"`: L4 only.

### 2. PII Training Requirement (Forbid)
- **Forbid** any action on a document where `containsPII == true` when
  the principal has NOT completed PII training
  (`principal.hasPIITraining == false`).
- This forbid applies to both `readDocument` and `downloadDocument`.
- The forbid is independent of the clearance/classification check: a
  user without PII training cannot access PII documents even with
  L4 clearance.

### 3. Need-to-Know for Restricted Documents (Forbid)
- **Forbid** any action on a Restricted document
  (`classification == "Restricted"`) when the principal is NOT in the
  document's `needToKnow` set. This applies to both actions.
- Users with L4 clearance who are NOT on the need-to-know list cannot
  access Restricted documents.

### 4. Download Access (Stricter)
A User may `downloadDocument` when their clearance is *one level
higher* than the document's classification per the download table:
- `classification == "Public"`: L2, L3, or L4 (not L1).
- `classification == "Internal"`: L3 or L4.
- `classification == "Confidential"`: L4 only.
- `classification == "Restricted"`: **no user may download**, even L4.

### 5. Reject Unknown Classifications
- The schema allows `classification` to be any `String`. For defensive
  policy writing, any document whose `classification` is not one of
  the four recognized values should be treated as the strictest tier
  (i.e., no access). However, this is an implementation-detail
  consideration and the policy is not required to explicitly handle
  unknown values — Cedar's default-deny behavior catches them.

## Notes
- The clearance-dominance check must be expressed as explicit string
  disjunctions, because Cedar has no enum ordering. For example, the
  read permit for Confidential data is
  `principal.clearance == "L3" || principal.clearance == "L4"`.
- The PII forbid applies to both actions. It is the cleanest to
  express as a single `forbid` rule scoped to both actions via
  `action in [Action::"readDocument", Action::"downloadDocument"]`.
- Same for the need-to-know forbid on Restricted documents.
- Common failure modes: (a) inverting the clearance ordering, (b)
  forgetting that "Restricted" excludes downloading entirely,
  (c) missing the need-to-know check and allowing any L4 user to
  access Restricted data, (d) missing the PII training gate.
