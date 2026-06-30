---
pattern: feature gating with capability tags (wide-set stress)
difficulty: hard
features:
  - Set<String> on both principal and resource
  - ".containsAll()" set subsumption check
  - 50 distinct string-literal capability predicates across the verification plan
  - many concrete (subscribed-set, required-set) liveness instantiations
domain: SaaS feature flags / entitlements
synthesis_difficulty: 3
---

# Wide Set 50 Elements — Policy Specification

## Context

A SaaS product gates access to features behind capability tags. Each
`User` carries a `subscribedFeatures: Set<String>` representing the
capability strings their plan grants. Each `Feature` resource carries a
`requiredCapabilities: Set<String>` enumerating the capabilities the
caller must have to invoke the feature.

The product catalog covers ~50 distinct capability strings
(`cap_001` ... `cap_050`), spanning analytics, billing, collaboration,
admin, AI, integrations, etc. The verification plan exercises 25
specific (feature, capability-subset) combinations that must remain
permitted under any correct synthesis. This stresses the synthesizer's
ability to handle a single uniform rule whose floor witnesses span a
wide string-predicate vocabulary.

## Requirements

### 1. useFeature

A `User` may `useFeature` on a `Feature` when the user's
`subscribedFeatures` contains ALL of the feature's `requiredCapabilities`:

```
principal.subscribedFeatures.containsAll(resource.requiredCapabilities)
```

There are no other paths to `useFeature` and no global forbids. A user
whose subscription is missing even one required capability must be denied.

### 2. Default Deny

All other requests are denied.
