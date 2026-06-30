---
pattern: subscription content gate
difficulty: medium
features:
  - string-enum hierarchy (plan vs content tier)
  - preview bypass (content flag overrides tier check)
  - action variants with different plan requirements
  - disjunctive tier encoding (no enum ordering in Cedar)
domain: streaming, SaaS
synthesis_difficulty: 3
---

# Subscription Content Gate -- Policy Specification

## Context

This policy implements a subscription-based content access pattern
common in streaming services and SaaS platforms. Every Subscriber has
a `plan` (one of `"free"`, `"basic"`, `"premium"`) and an `isActive`
flag. Every Content item has a `tier` (one of `"free"`, `"basic"`,
`"premium"`) and an `isPreview` flag.

Three actions exist: `stream`, `download`, and `share`. Each action
has different plan requirements, and all require the subscriber to be
active.

## Plan / Tier Hierarchy

The ordering is `free < basic < premium`. A subscriber's plan
"dominates" a content tier when the plan is at least as high as the
tier. Because Cedar has no enum ordering, this must be expressed as
explicit string disjunctions.

| Content tier | Plans that dominate |
|--------------|---------------------|
| free         | free, basic, premium |
| basic        | basic, premium       |
| premium      | premium only         |

## Requirements

### 1. Stream Access

A Subscriber may `stream` Content when:
- The subscriber is active (`isActive == true`), AND
- EITHER the content is a preview (`isPreview == true`), OR the
  subscriber's plan dominates the content's tier.

The preview flag allows any active subscriber to stream preview
content regardless of plan. Non-preview content requires plan
dominance.

### 2. Download Access

A Subscriber may `download` Content when:
- The subscriber is active (`isActive == true`), AND
- The subscriber's plan is `"basic"` or `"premium"` (free-plan
  subscribers cannot download anything), AND
- The subscriber's plan dominates the content's tier.

Note: the preview flag does NOT bypass the download restriction.
Free-plan subscribers cannot download even preview content.

### 3. Share Access

A Subscriber may `share` Content when:
- The subscriber is active (`isActive == true`), AND
- The subscriber's plan is `"premium"`.

Sharing is unrestricted by content tier -- premium subscribers may
share any content. But only premium subscribers have this capability.

### 4. Inactive Subscribers

Inactive subscribers (`isActive == false`) are denied ALL actions
regardless of plan or content tier. This is enforced by requiring
`isActive == true` in every permit rule; Cedar's default-deny
behavior handles the rest.

## Notes

- The plan-dominance check uses explicit disjunctions because Cedar
  has no built-in enum ordering. For example, the stream permit for
  `tier == "basic"` content requires
  `principal.plan == "basic" || principal.plan == "premium"`.
- The preview bypass applies ONLY to streaming, not downloading or
  sharing. This is a deliberate design choice reflecting a "try
  before you buy" pattern.
- Common failure modes: (a) allowing free-plan downloads, (b)
  applying the preview bypass to download, (c) forgetting the
  isActive gate, (d) inverting the tier hierarchy.
