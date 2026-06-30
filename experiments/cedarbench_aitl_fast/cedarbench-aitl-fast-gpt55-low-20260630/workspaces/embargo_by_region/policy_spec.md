---
pattern: regional embargo with per-region release datetimes
difficulty: medium
features:
  - per-region datetime branch on user attribute
  - duration arithmetic for anti-leak buffer
  - explicit branching (no dynamic record key access)
domain: media / content distribution
synthesis_difficulty: 3
---

# Embargo By Region -- Policy Specification

## Context

This policy governs access to embargoed media assets that release on
different schedules in different regions. Each `Asset` carries three
independent release datetimes -- one for the United States, one for
Europe, and one for Asia-Pacific. A `User` is associated with exactly
one region, and the user's region selects which release datetime
applies when the system decides whether to grant access.

Entities:
- `User` with `region: String` (one of `"us"`, `"eu"`, `"apac"`).
- `Asset` with `releaseUS: datetime`, `releaseEU: datetime`,
  `releaseAPAC: datetime`.

Context:
- `now: datetime` -- current wall-clock time, supplied by the host
  application.

Two actions:
- `view` -- lightweight viewing of a released asset.
- `download` -- more sensitive; grants the user a local copy.

### Cedar idiom note

Cedar records do NOT support dynamic key access -- there is no way to
write something like `resource[principal.region]`. The release datetime
that applies to a given request must be selected via an explicit
branch on each region value:

```
permit (...) when {
    (principal.region == "us"   && context.now >= resource.releaseUS)
    || (principal.region == "eu"   && context.now >= resource.releaseEU)
    || (principal.region == "apac" && context.now >= resource.releaseAPAC)
};
```

## Requirements

### 1. View After Regional Release (Permit)

A `User` may perform the `view` action on an `Asset` only when the
current time is at or after the release datetime for the user's
region:

- A user in `"us"` may view once `context.now >= resource.releaseUS`.
- A user in `"eu"` may view once `context.now >= resource.releaseEU`.
- A user in `"apac"` may view once `context.now >= resource.releaseAPAC`.

Before the regional release datetime, the user may NOT view the
asset, even if the asset has already released in another region.

### 2. Download After Regional Release Plus Anti-Leak Buffer (Permit)

A `User` may perform the `download` action on an `Asset` only when
the current time is at or after the release datetime for the user's
region PLUS a 24-hour anti-leak buffer:

- A user in `"us"` may download once
  `context.now >= resource.releaseUS + 24h`.
- A user in `"eu"` may download once
  `context.now >= resource.releaseEU + 24h`.
- A user in `"apac"` may download once
  `context.now >= resource.releaseAPAC + 24h`.

The anti-leak buffer gives the rights team a 24-hour window after a
regional release to pull the asset back without local copies having
been distributed. During the first 24 hours after a regional release
the asset is viewable (streaming) but NOT downloadable.

### 3. Region Cross-Wiring -- Forbidden

The release datetime that gates a request MUST be the one for the
user's own region. Using another region's release datetime (e.g.
checking `releaseEU` for a US user) is a bug, even if it happens to
permit a "true" request. The policy must branch explicitly on
`principal.region`.

### 4. Single Release Datetime -- Forbidden

The policy MUST NOT collapse the three release datetimes into a single
condition (e.g. by using only `releaseUS`, or by taking the minimum).
Each region has its own release schedule and must be enforced
independently.

## Notes

- The three region strings are exactly `"us"`, `"eu"`, and `"apac"`.
  No other region values exist; users with any other region value
  receive no permit.
- `duration("24h")` is Cedar's Go-style duration syntax for 24 hours.
  ISO 8601 duration syntax (`"P1D"`, `"PT24H"`) is rejected by Cedar.
- The 24-hour buffer is applied as
  `resource.release<REGION>.offset(duration("24h"))` -- i.e. the
  release datetime shifted forward by 24 hours. The download is
  permitted once `context.now` reaches this shifted instant.
- Cedar denies by default, so the absence of a permit for a request
  before the regional release (or before release + 24h, for
  downloads) is sufficient.
