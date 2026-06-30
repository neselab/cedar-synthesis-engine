---
pattern: resource budget enforcement (quota-based access)
difficulty: medium
features:
  - numeric comparison for budget/quota checks
  - context-provided usage counters
  - tier-based resource limits
domain: cloud platform / SaaS billing
synthesis_difficulty: 2
---

# Resource Budget Enforcement — Policy Specification

## Context

A cloud platform where `Tenant` principals provision `Resource`
instances. Each tenant has a `tier` (`"free"`, `"pro"`, `"enterprise"`)
and the host application passes the current `usageCount` (how many
resources the tenant currently has) in the request context.

This scenario tests the pattern where the authorization decision
depends on a numeric comparison between a context-provided counter
and a tier-derived limit.

## Requirements

### 1. Create — Within Budget
A Tenant may `create` a Resource when:
- Tier `"free"`: `context.usageCount < 5` (max 5 resources)
- Tier `"pro"`: `context.usageCount < 50` (max 50 resources)
- Tier `"enterprise"`: always permitted (unlimited)

### 2. Read — Always Permitted
A Tenant may `read` any of their own Resources. Since the schema
doesn't model ownership (to keep the focus on quota logic), read
is permitted for any Tenant on any Resource.

### 3. Delete — Always Permitted
A Tenant may `delete` any Resource (deleting frees quota).

### 4. Upgrade — Enterprise Only
A Tenant may `upgrade` a Resource (e.g. increase compute) when:
- The tenant's tier is `"pro"` or `"enterprise"`.

Free-tier tenants cannot upgrade resources.

### 5. Default Deny
All other requests are denied.
