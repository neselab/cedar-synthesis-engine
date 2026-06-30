---
pattern: content moderation tiered escalation
difficulty: medium
features:
  - trust level hierarchy (numeric comparison)
  - severity-based action routing
  - escalation chain (junior → senior → lead)
domain: social media / content platforms
synthesis_difficulty: 4
---

# Content Moderation Escalation — Policy Specification

## Context

A social media platform where `ContentReport` resources represent
flagged content reports with a `severity` level (1–5, where 5 is
most severe). Moderators (`Moderator` entity) have a numeric
`trustLevel` (1–3).

The policy implements a tiered escalation model: low-severity reports
can be handled by junior moderators, while high-severity reports
require senior or lead moderators.

## Requirements

### 1. Review — Trust Level Must Meet Severity Threshold
A Moderator may `review` a ContentReport when:
- Severity 1–2: any moderator (trustLevel >= 1)
- Severity 3: trustLevel >= 2
- Severity 4–5: trustLevel >= 3

Encoding: `principal.trustLevel * 2 >= resource.severity` captures
this threshold (trustLevel 1 handles severity <=2, trustLevel 2
handles <=4, trustLevel 3 handles all).

Actually, more precisely:
- `principal.trustLevel >= 1 && resource.severity <= 2`, OR
- `principal.trustLevel >= 2 && resource.severity <= 4`, OR
- `principal.trustLevel >= 3`

### 2. Resolve — Same Threshold as Review
A Moderator may `resolve` a ContentReport under the same trust-level
rules as review (same threshold mapping).

### 3. Escalate — Anyone Can Escalate
A Moderator may `escalate` any ContentReport regardless of trust
level. Escalation is always permitted — a junior moderator who
encounters a report beyond their authority should escalate it.

### 4. Override — Lead Moderators Only
A Moderator may `override` a previous resolution on a ContentReport
when:
- `principal.trustLevel >= 3` (lead moderators only).

### 5. Default Deny
All other requests are denied.
