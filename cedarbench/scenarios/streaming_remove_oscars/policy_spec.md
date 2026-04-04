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

### 3. Early Access for Premium Subscribers
- A **Subscriber** with `subscription.tier == "premium"` may **watch** a Show
  that has `isEarlyAccess == true` even before the `releaseDate`, as long as
  the current time is within 24 hours before the `releaseDate`
  (i.e. `context.now.datetime >= resource.releaseDate.offset(duration("-24h"))`).

### 4. Kid Bedtime Restriction (Deny Rule)
- If a Subscriber's `profile.isKid == true`, the **watch** action is forbidden
  outside of 6:00 AM to 9:00 PM local time.
  Local time is computed using `context.now.datetime.offset(context.now.localTimeOffset)`.
  Specifically, forbid watch when the local time-of-day is before 06:00 or at/after 21:00.

## Notes
- Cedar denies by default — no explicit deny-by-default needed.
- There are no rent/buy actions or Oscar promo rules in this variant.
- The only temporal rules are early access and bedtime.
