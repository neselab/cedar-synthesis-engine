# Streaming Service — Policy Specification

## Context

This policy governs access control for a streaming video platform with
FreeMember and Subscriber principals, and Movie and Show resources.

Subscribers have a `subscription` with a `tier` (e.g. "standard", "premium")
and a `profile` with an `isKid` boolean.

## Requirements

### 1. Subscriber Watch Permissions
- A **Subscriber** may **watch** any Show, UNLESS the show has `isEarlyAccess == true`
  AND the current time (`context.now.datetime`) is before the show's `releaseDate`.
- A **Subscriber** may **watch** any Movie, UNLESS the movie has `needsRentOrBuy == true`.

### 2. FreeMember Watch Permissions
- A **FreeMember** may **watch** any Movie where `isFree == true`.
- A **FreeMember** may **watch** any Show where `isFree == true`.

### 3. Oscar Promo (Rent/Buy Window)
- A **Subscriber** may **rent** or **buy** a Movie IF the movie has `isOscarNominated == true`
  AND the current time is within the Oscar promo window:
  `datetime("2025-02-01T00:00:00Z")` to `datetime("2025-03-31T23:59:59Z")`.

### 4. Early Access for Premium Subscribers
- A **Subscriber** with `subscription.tier == "premium"` may **watch** a Show
  that has `isEarlyAccess == true` even before the `releaseDate`, as long as
  the current time is within 24 hours before the `releaseDate`
  (i.e. `context.now.datetime >= resource.releaseDate.offset(duration("-24h"))`).

### 5. Kid Bedtime Restriction (Deny Rule)
- If a Subscriber's `profile.isKid == true`, the **watch** action is forbidden
  outside of 6:00 AM to 9:00 PM local time.
  Local time is computed using `context.now.datetime.offset(context.now.localTimeOffset)`.
  Specifically, forbid watch when the local time-of-day is before 06:00 or at/after 21:00.

## Notes
- Cedar denies by default — no explicit deny-by-default needed.
- Temporal comparisons use Cedar's `datetime` and `duration` extension types.
- The bedtime rule is a `forbid` that overrides any `permit`.
### 6. Download Permissions
- A **Subscriber** may **download** any Movie or Show, UNLESS the content has `isFree == true`.
  (Free content is streaming-only and cannot be downloaded.)
- A **FreeMember** may NOT download any content (not a valid principal for download).

### 7. Geo-Restriction (Deny Rule)
- Each Movie and Show has an `allowedRegions` attribute (`Set<String>` of region codes).
- The **watch** action's context includes `region: String`.
- If `!resource.allowedRegions.contains(context.region)`, the **watch** action is forbidden.
- Geo-restriction applies to all principals (FreeMember and Subscriber).
- The rent, buy, and download actions are NOT geo-restricted.

### 8. Age Rating Restriction (Deny Rule)
- Each Movie and Show has a `rating: String` attribute with values: `"G"`, `"PG"`, `"PG13"`, or `"R"`.
- If a Subscriber's `profile.isKid == true`, the **watch** action is forbidden
  on content where `rating` is NOT `"G"` and NOT `"PG"`.
  (Kid profiles can only watch G or PG rated content.)
- Non-kid Subscribers and FreeMember principals are NOT restricted by rating.

## Notes (Full Expansion)
- This scenario combines THREE new constraints on top of the base rules:
  (a) download action with free-content restriction,
  (b) geo-restriction via set membership,
  (c) age rating restriction for kid profiles.
- Four independent forbid rules may apply: bedtime, geo-restriction, age rating, and free-download block.
- The download action has no context (no temporal or geographic constraints).
