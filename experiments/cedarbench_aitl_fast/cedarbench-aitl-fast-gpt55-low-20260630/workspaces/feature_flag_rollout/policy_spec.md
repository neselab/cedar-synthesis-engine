---
pattern: feature flag rollout
difficulty: medium
features:
  - boolean flag
  - percentage-based rollout via numeric comparison
  - role override
domain: SaaS platform
synthesis_difficulty: 2
---

# Feature Flag Rollout

## Context

This scenario models a feature-flag system for gradual rollout in a SaaS
platform. Each user is assigned a deterministic `rolloutBucket` (0-99) via
a hash of their user ID. Features have a boolean `isEnabled` master switch
and a `rolloutPercentage` (0-100) that controls what fraction of users can
access the feature.

The pattern tests numeric comparison (`rolloutBucket < rolloutPercentage`),
boolean attribute checks, and string-based role overrides that bypass the
rollout gate.

## Entities

- **User** -- principal. Has a `role` string (`"user"`, `"beta_tester"`,
  or `"admin"`) and a `rolloutBucket` long (0-99).
- **Feature** -- resource. Has an `isEnabled` boolean master switch and a
  `rolloutPercentage` long (0-100) controlling gradual rollout.

## Actions

- **use** -- access a feature in production.
- **preview** -- access a feature in preview/staging mode.
- **configure** -- change feature flag settings (toggle, percentage, etc.).

## Requirements

### Action: use

A User may **use** a Feature when ALL of the following hold:

1. The feature's `isEnabled` flag is `true`, AND
2. At least one of:
   - The user's `role` is `"beta_tester"`, OR
   - The user's `role` is `"admin"`, OR
   - The user's `rolloutBucket` is strictly less than the feature's
     `rolloutPercentage`.

This models a common pattern: beta testers and admins always get access to
enabled features, while regular users are gradually rolled in as the
percentage increases.

Floors:
- A beta tester MUST be permitted to use an enabled feature (regardless of
  their rollout bucket value).
- A user whose `rolloutBucket` is strictly less than the feature's
  `rolloutPercentage` MUST be permitted to use that feature when it is
  enabled.

### Action: preview

A User may **preview** a Feature when:

- The user's `role` is `"beta_tester"` OR `"admin"`.

Preview access is independent of the feature's `isEnabled` flag and
`rolloutPercentage`. This lets testers and admins evaluate features before
they are enabled or rolled out to any users.

Floor:
- A beta tester MUST be permitted to preview any feature.

### Action: configure

A User may **configure** a Feature when:

- The user's `role` is `"admin"`.

Only admins can change feature flag settings.

Floor:
- An admin MUST be permitted to configure any feature.

### Liveness

Each of the three actions must permit at least one request. No action
should end up globally denied.

## Out of scope

- No temporal constraints (feature expiry, time windows).
- No per-feature override lists or allowlists beyond the role check.
- No global forbids.
- No entity hierarchy or group membership.
