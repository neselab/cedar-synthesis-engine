---
pattern: redundant spec restating the same single rule
difficulty: easy
features:
  - planner deduplication of restated requirements
  - single owner-only access rule
  - encoding-once discipline
domain: document storage
synthesis_difficulty: 1
---

# Redundant Spec — Single Rule Restated Three Ways

## Context

A minimal document storage system where each `Document` has exactly one
`owner` (a `User`), and the only supported action is `read`. The
specification deliberately states the SAME requirement three different
ways using three different phrasings. The planner is being tested on
its ability to recognize the redundancy and encode the rule ONCE,
not three times.

## Requirements

### 1. Owner-Only Read (Statement A)
A user can read a document only if they are the owner of that document.

### 2. Owner-Only Read (Statement B)
Document access for the `read` action is restricted to the document's
owner.

### 3. Owner-Only Read (Statement C)
Read permissions are scoped to the principal who owns the resource.

### Note on Redundancy

Statements 1, 2, and 3 above are **the same rule** restated in three
different ways. They all reduce to:

```
permit when principal == resource.owner
```

The correct encoding contains exactly ONE permit policy expressing this
rule. There should not be three separate (semantically identical) policies,
nor should the rule be split across multiple ceilings/floors as if the
three statements imposed different constraints.

### 4. Default Deny
All other requests (non-owner read attempts) are denied.
