---
pattern: missing edge case (empty set / empty string default-deny)
difficulty: hard (planning)
features:
  - set membership
  - empty-set / empty-string default-deny
  - safe-default planner inference
  - implicit edge-case handling
domain: document tagging / search
synthesis_difficulty: 4
---

# Missing Edge Case: Empty Set -- Policy Specification

## Context

This policy governs viewing a `Document` "by tag." A `Document` carries
a `tags: Set<String>` attribute, and a `viewByTag` request supplies
`context.requestedTag: String`. The host application uses this rule
to gate tag-filtered listing/search results.

## The deliberately-silent specification

The product team wrote a single sentence:

> "A user can view a document by tag when the document has the
> requested tag in its tag set."

That is the entire functional requirement. The spec is **deliberately
silent** about two edge cases that arise in practice:

1. What happens when `resource.tags` is the empty set (the document
   has no tags at all)?
2. What happens when `context.requestedTag` is the empty string (the
   client sent an empty filter)?

Cedar's `Set::contains` returns `false` for an empty set, and Cedar
strings are total (`""` is a valid string). So a literal reading of the
spec ("contains the requested tag") would correctly deny the empty-set
case but would *permit* a request for an empty-string tag if some buggy
upstream had inserted `""` into a document's tag set, or if the client
exploited an empty-string filter to enumerate documents.

This scenario tests whether the planner picks the **safe default**
(deny on edge cases) when the spec does not explicitly mention them.

## Requirements

### 1. Permit the documented happy path
A `User` may perform `viewByTag` on a `Document` when ALL of:
  - the document's `tags` set is non-empty,
  - the requested tag is a non-empty string,
  - the document's `tags` set contains the requested tag.

### 2. Implicit safe-default deny on edge cases (planner inference)
The spec is silent on these, but the planner MUST encode them as deny:
  - If `resource.tags.isEmpty()`, deny.
  - If `context.requestedTag == ""`, deny.

Cedar's default-deny semantics already deny these cases if the permit
clause is correctly guarded. There is no need for an explicit `forbid`,
but the permit's `when` clause MUST include the `!isEmpty()` and
`!= ""` guards rather than relying solely on `Set::contains` returning
the "right" thing for adversarial inputs.

### 3. Floors (positive assertions for the documented happy path only)
- A `User` requesting `viewByTag` where `context.requestedTag == "public"`
  on a `Document` whose `tags` contains `"public"` MUST be permitted.
- A `User` requesting `viewByTag` where `context.requestedTag == "draft"`
  on a `Document` whose `tags` contains `"draft"` MUST be permitted.

There is **no floor** for the empty-set or empty-string cases. Adding
one would contradict the implied default-deny semantics this scenario
is designed to test.

## Notes
- Cedar denies by default, so the safe-default behavior is achieved
  by guarding the permit, not by writing a forbid.
- The planner's job here is to **add safety guards the spec did not
  request**. A naive transcription of the spec sentence would write
  `permit when { resource.tags.contains(context.requestedTag) }`,
  which is unsafe when `requestedTag == ""` and a stray `""` tag
  appears in document data.
- Schema does not declare `tags` as a non-empty set (Cedar has no such
  type), so the policy is the only place this invariant can live.
