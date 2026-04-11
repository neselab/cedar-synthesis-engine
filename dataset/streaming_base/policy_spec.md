# Streaming Service — Policy Specification

## Context

This policy governs access control for an on-demand streaming service that
delivers Movies and Shows to two kinds of members: free members and paid
subscribers. Paid subscribers come in two tiers, *standard* and *premium*.
Some content is free, some requires a paid subscription, some requires
renting or buying, some is offered in *Early Access* before its official
release date, and some Movies are nominated for the Oscars and offered for
rent/buy in the month leading up to the awards. Subscribers may have a *kid
profile* enabled on their account, which forbids watching during bedtime
hours.

The schema relies on the experimental `datetime` extension. Rules involving
release dates and bedtime use `datetime` and `duration` values from the
request context.

## Entity Model

- **FreeMember** is an unpaid member.
- **Subscriber** is a paid member. Each Subscriber has:
  - `subscription: { tier: String }` where `tier` is either `"standard"` or
    `"premium"`.
  - `profile: { isKid: Bool }` — whether the kid profile is enabled.
- **Movie** has:
  - `isFree: Bool` — whether the movie can be watched for free.
  - `needsRentOrBuy: Bool` — whether the movie can only be accessed via
    rent or buy (i.e., not included in the standard subscriber catalog).
  - `isOscarNominated: Bool` — whether the movie is nominated for the
    Oscars.
- **Show** has:
  - `isFree: Bool` — whether the show can be watched for free.
  - `releaseDate: datetime` — the show's official release datetime.
  - `isEarlyAccess: Bool` — whether the show is currently in early access
    (i.e., available to premium subscribers up to 24 hours before
    `releaseDate`).
- **Context** carries `now: { datetime: datetime, localTimeOffset: duration }`
  for `watch` requests, and `now: { datetime: datetime }` for `rent`/`buy`
  requests. The `localTimeOffset` is used to compute local clock time for
  the kid-profile bedtime check.

## Actions

- **watch** — applies to either Movie or Show, with principals FreeMember
  or Subscriber.
- **rent**, **buy** — apply only to Movies, with principals FreeMember or
  Subscriber.

## Requirements

### 1. Free Content Access (FreeMember)
- A `FreeMember` may **watch** any content (Movie or Show) only if
  `resource.isFree == true`. Free members may not rent or buy.

### 2. Subscriber Access to Shows
- A `Subscriber` (any tier) may **watch** any `Show` provided the show is
  not currently in early access. Concretely: permit `watch` on a Show if
  the principal is a Subscriber and the show is past its early-access
  window. Free shows are also watchable via rule §1.

### 3. Subscriber Access to Movies
- A `Subscriber` (any tier) may **watch** any `Movie` that does NOT require
  rent-or-buy. That is: `resource.needsRentOrBuy == false`. Movies that
  require rent-or-buy are excluded from the standard subscriber catalog
  and must be paid for separately via rule §4.

### 4. Rent or Buy Oscar-Nominated Movies
- During the month leading up to Oscars night, any member (FreeMember or
  Subscriber) may **rent** or **buy** an Oscar-nominated Movie. The rule
  is satisfied when:
  - `resource.isOscarNominated == true`, AND
  - `context.now.datetime` falls within the one-month window ending on
    Oscars night. (For the test data set, Oscars night is in early March;
    the policy should be expressible in terms of the Oscars datetime
    using the `datetime` constructor and `offset`/comparison methods.)
- Rent or buy of non-Oscar-nominated Movies, or outside the window, is
  not granted by this rule.

### 5. Early Access to Shows (Premium Subscribers Only)
- A `Subscriber` whose `subscription.tier == "premium"` may **watch** a
  `Show` during its early-access window — that is, up to 24 hours before
  `resource.releaseDate`. Concretely:
  - `principal.subscription.tier == "premium"`, AND
  - `context.now.datetime` is within `(releaseDate - 24h)` to `releaseDate`,
    using the `duration` constructor and a 24-hour offset.
- Standard-tier subscribers cannot watch a Show in its early-access
  window. Once the show's `releaseDate` has passed, all subscribers may
  watch it via rule §2.

### 6. Kid Profile Bedtime Forbid
- For any `Subscriber` whose `profile.isKid == true`, **forbid** the
  `watch` action between bedtime hours. Bedtime is defined as the local
  clock time (after applying `context.now.localTimeOffset` to
  `context.now.datetime`) being later than `21:00` (9 PM) or earlier
  than `06:00` (6 AM). The local time-of-day is computed using the
  `duration` constructor and `toTime` method on the offset-adjusted
  datetime.
- This is a forbid rule that overrides any of the watch permits above.
  It applies only to Subscribers with the kid profile enabled and only
  to the `watch` action.

## Notes
- Cedar denies by default. Permits in §1–§5 grant the listed accesses;
  the forbid in §6 overrides them for kid profiles during bedtime.
- The `watch` action accepts both `Movie` and `Show` as resource types,
  and both `FreeMember` and `Subscriber` as principal types. Each rule
  must use Cedar's type discrimination (e.g., `principal is Subscriber`,
  `resource is Show`) to apply only to the relevant combinations.
- All datetime/duration arithmetic uses Cedar's experimental `datetime`
  extension. The schema commits to this — Cedar must be built with
  `--features datetime` for the policy to validate.
- The `localTimeOffset` is per-request and supplied in the context; the
  policy itself does not need to know the user's home timezone.
