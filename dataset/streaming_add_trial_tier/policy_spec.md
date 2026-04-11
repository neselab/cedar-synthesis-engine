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
### 6. TrialMember Permissions
- A **TrialMember** has a `trialExpiry: datetime` attribute.
- A TrialMember may **watch** any Movie or Show where `isFree == true` (same as FreeMember).
- A TrialMember may ALSO **watch** non-free Movies (where `isFree == false` and `needsRentOrBuy == false`)
  as long as the trial has not expired: `context.now.datetime < principal.trialExpiry`.
- A TrialMember may ALSO **watch** non-free Shows (where `isFree == false` and `isEarlyAccess == false`)
  as long as the trial has not expired: `context.now.datetime < principal.trialExpiry`.
- Once the trial expires, a TrialMember can only watch free content (same as FreeMember).
- A TrialMember may NOT **rent** or **buy** movies (they are not a valid principal for those actions).

## Notes (Trial Tier)
- The TrialMember is a new entity type distinct from FreeMember and Subscriber.
- Temporal expiry check compares `context.now.datetime` against `principal.trialExpiry`.
- TrialMembers do NOT get early access or Oscar promo benefits.
