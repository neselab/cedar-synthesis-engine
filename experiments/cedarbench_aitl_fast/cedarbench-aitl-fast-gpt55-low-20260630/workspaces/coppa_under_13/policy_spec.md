---
pattern: COPPA under-13 verifiable parental consent
difficulty: hard
features:
  - optional context attribute (`has` guarding)
  - duration arithmetic on dateOfBirth
  - asymmetric rules (collect vs. share) for the same data
  - data-subject vs. requesting-principal age check
  - COPPA-stricter rule (under-13 personal data unshareable even with consent)
domain: privacy / regulatory compliance
synthesis_difficulty: 4
---

# COPPA: Under-13 Verifiable Parental Consent

## Background

The Children's Online Privacy Protection Act (COPPA, 16 CFR Part 312)
regulates the online collection of personal information from children
under 13 in the United States. The relevant operational requirements
for a policy engine are:

1. **Collection of personal data on under-13 users requires verifiable
   parental consent** (16 CFR §312.5).
2. **Anonymous data is exempt** — collection of data that does not
   constitute "personal information" under §312.2 carries no consent
   requirement.
3. **13 and older are out of COPPA scope** — once a data subject is 13
   or older, no parental consent is required (other regimes such as
   CCPA / GDPR may apply, but those are out of scope here).
4. **Children's personal data may not be disclosed to third parties**
   even when parental consent has been obtained for collection
   (the COPPA-stricter rule for sharing). In this scenario "personal"
   data is therefore never shareable for any data subject; for under-13
   subjects the prohibition is absolute even with a consent token.

## Schema

- `User` with `dateOfBirth: datetime`
- `DataPoint` with `owner: User` and `category: String` —
  one of `"anonymous"`, `"behavioral"`, `"personal"`, `"geolocation"`
- Actions: `collect`, `share`, `delete` on (`User`, `DataPoint`)
- Context for `collect` and `share`:
  - `now: datetime` (current wall-clock time)
  - `parentalConsentToken?: String` — **optional**, present when the
    host application has collected verifiable parental consent per
    §312.5. The policy treats presence as proof of consent.
- Context for `delete`: just `now: datetime`.

The age threshold for "under 13" is `< 4748 days`, the conservative
leap-year-safe day count matching the convention established in
`age_verification_leap_years` (13×365 + 3 leap days, choosing the
threshold such that any user with that many days has indisputably
had their 13th birthday in any plausible leap-year alignment).

## Rules

**collect:**
- Anonymous data (`category == "anonymous"`): permitted for any user,
  any age, no consent required.
- Personal / behavioral / geolocation:
  - 13+ (`now.durationSince(principal.dateOfBirth) >= duration("4748d")`):
    permitted, no consent required.
  - Under 13 (`< duration("4748d")`): permitted only if
    `context has parentalConsentToken`.

**share:**
- Anonymous data: always permitted (no PII).
- Behavioral / geolocation: permitted only if the **data subject**
  (`resource.owner`, NOT the requesting principal) is 13+.
- Personal data: **NEVER permitted**, regardless of age, regardless of
  whether parental consent has been obtained.

**delete:**
- Permitted only when `principal == resource.owner`. Owners may always
  request deletion of their own data (this satisfies COPPA §312.6 as
  well as general data-subject deletion rights).

## Failure modes this scenario hunts

- **§8.3 negated-`has` trap.** Cedar's type-checker does not propagate
  negation through `has`, so the natural-looking guard
  `!(context has parentalConsentToken) || ...` is rejected. Candidates
  must use either presence-as-permission (`context has parentalConsentToken`)
  or the verbose form
  `(!(context has X) || (context has X && context.X.something))`.
- **Age check on the wrong party.** For `share`, the COPPA protection
  attaches to the **data subject** (`resource.owner.dateOfBirth`), not
  the requesting principal. Candidates that reuse the collect-action
  age expression on principal will over-permit when an adult shares a
  child's data.
- **Consent permits collection, not sharing.** A candidate that treats
  `parentalConsentToken` as a universal override for under-13
  restrictions will violate the share ceiling.
- **Naive year-to-day conversion / wrong duration syntax.** Cedar's
  `duration()` requires a string-literal argument in Go-style format
  (`"4748d"`), and ISO-8601 (`"P4748D"`) is rejected.
- **Forgetting one of the three actions.** Candidates that only handle
  `collect` and `share` will fail the delete liveness/floor.

## Verification plan summary

11 checks: 3 ceilings (collect, share, delete) + 5 floors (anonymous
collection, 13+ personal collection, under-13 with-consent collection,
13+ behavioral sharing, owner deletion) + 3 liveness (one per action).
