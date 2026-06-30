---
pattern: forbid with specific exception (weakened-forbid idiom)
difficulty: medium
features:
  - global forbid with narrow exception
  - permits cannot override forbids — must weaken the forbid condition
  - per-action exception asymmetry (view has owner exception, edit does not)
domain: document management / records retention
synthesis_difficulty: 3
---

# Forbid with Specific Exception — Policy Specification

## Context

A document management system with a retention model. Documents can
be `archived: Bool`. Once archived, documents are read-only for the
owner (records retention) and inaccessible to everyone else. Editing
an archived document is forbidden for ALL users including the owner —
archived documents are immutable.

This scenario tests the canonical Cedar idiom for "global forbid with
a narrow exception." A naive author writes:

```cedar
forbid (principal, action == Action::"view", resource is Document)
when { resource.archived };
permit (principal, action == Action::"view", resource is Document)
when { principal == resource.owner };
```

This is WRONG. Cedar permits cannot override forbids. The owner's
permit is silently shadowed. The correct idiom is to WEAKEN the
forbid condition itself:

```cedar
forbid (principal, action == Action::"view", resource is Document)
when { resource.archived && !(principal == resource.owner) };
```

## Entities

- `User` — system principal.
- `Document` — has `archived: Bool` and `owner: User`.

## Actions

- `view`
- `edit`

## Requirements

### 1. View — Generally Permitted, Forbidden When Archived (Owner Exception)

A User may `view` a Document when:
- The document is NOT archived (anyone can view), OR
- The document IS archived AND the user is the owner (read-only retention access).

A User may NOT `view` a Document when:
- The document IS archived AND the user is NOT the owner.

### 2. Edit — Owner Only, Always Forbidden When Archived

A User may `edit` a Document when:
- The user is the owner AND the document is NOT archived.

A User may NOT `edit` a Document when:
- The user is not the owner, OR
- The document is archived (regardless of ownership — no exception).

### 3. Default Deny

All other requests are denied.
