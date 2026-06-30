---
pattern: policy annotations (@id / @description)
difficulty: easy
features:
  - "@id" annotation on each policy rule
  - "@description" annotation on each policy rule
  - simple RBAC baseline to keep semantic complexity low
domain: content management
synthesis_difficulty: 1
---

# Policy Annotations — Policy Specification

## Context

A simple content management system with `User` principals who have a
`role` attribute (`"viewer"`, `"editor"`, `"admin"`). Resources are
`Article` entities with an `isPublished` boolean.

This scenario is deliberately simple in its access-control semantics.
The interesting dimension is that every rule MUST carry `@id("...")`
and `@description("...")` Cedar annotations. These annotations are
first-class Cedar syntax (not comments) and are preserved by the
parser. They serve as machine-readable policy identifiers and
human-readable explanations in auditing and compliance workflows.

## Requirements

### 1. Viewer — Read Published Only
- A User whose `role` is `"viewer"` may `read` an Article when
  `resource.isPublished == true`.

### 2. Editor — Read and Write
- A User whose `role` is `"editor"` may `read` any Article
  (published or not).
- A User whose `role` is `"editor"` may `write` any Article.

### 3. Admin — Full Access
- A User whose `role` is `"admin"` may `read`, `write`, and `delete`
  any Article.

### 4. Default Deny
All other requests are denied.

### 5. Annotation Requirement
Every `permit` and `forbid` rule in the synthesized policy MUST carry
both `@id("...")` and `@description("...")` annotations. The `@id`
should be a short kebab-case identifier (e.g. `"viewer-read-published"`).
The `@description` should be a one-sentence English explanation of what
the rule does.
