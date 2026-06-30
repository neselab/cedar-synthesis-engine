---
pattern: CI/CD deployment gate
difficulty: medium
features:
  - role-based environment promotion
  - boolean precondition gating (test pass)
  - string equality on resource attribute (environment)
  - three-action authorization surface
domain: DevOps
synthesis_difficulty: 2
---

# CI/CD Deployment Gate

## Context

A CI/CD pipeline controls which users can promote artifacts to different
environments. Three environments exist (dev, staging, production), with
progressively stricter authorization. Pipeline users have a string role
("developer", "lead", "releaseManager") and an `isCodeOwner` boolean.
Deployments carry the target environment and whether the test suite passed.

## Entities

- **PipelineUser** (principal): has `role` (String) and `isCodeOwner` (Bool).
- **Deployment** (resource): has `environment` (String: "dev", "staging",
  "production") and `hasPassedTests` (Bool).

## Actions

- **deploy** -- promote an artifact to the target environment.
- **rollback** -- revert the target environment to its previous version.
- **approve** -- sign off on a deployment for production release.

## Requirements

### Action: deploy

A deployment is permitted when ALL of the following hold:

1. The deployment has passed tests (`resource.hasPassedTests == true`).
2. The environment-specific role gate is satisfied:
   - **dev**: any role may deploy.
   - **staging**: the user's role must be "lead" or "releaseManager".
   - **production**: the user's role must be "releaseManager".

Floors:
- A developer with passing tests MUST be permitted to deploy to dev.
- A lead with passing tests MUST be permitted to deploy to staging.
- A releaseManager with passing tests MUST be permitted to deploy to production.

### Action: rollback

A rollback is permitted when the user's role is "lead" or "releaseManager".
No test-pass requirement (rollbacks are emergency actions).

Floor:
- A lead MUST be permitted to rollback any environment.

### Action: approve

An approval is permitted when the user's role is "releaseManager".

Floor:
- A releaseManager MUST be permitted to approve.

### Liveness

Each action (deploy, rollback, approve) must permit at least one request.

## Out of scope

- No time-of-day or maintenance-window constraints.
- No multi-approval quorum.
- No global forbids (no revocation, suspension, etc.).
