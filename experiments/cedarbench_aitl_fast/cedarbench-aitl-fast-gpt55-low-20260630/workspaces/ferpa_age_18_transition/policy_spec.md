---
pattern: FERPA age-of-majority transition for educational records
difficulty: hard
features:
  - datetime arithmetic
  - duration comparison
  - role-based access with age-conditional revocation
  - parental rights transfer
domain: education / regulatory compliance
synthesis_difficulty: 4
---

# FERPA Age-18 Transition -- Policy Specification

## Context

This policy implements the core FERPA (Family Educational Rights and Privacy
Act) rule that parental rights to access a student's educational records
**transfer to the student** when the student turns 18. Before age 18, a
parent or legal guardian may inspect, request correction of, and (in some
contexts) be notified about disclosure of the student's records. On the
student's 18th birthday (the "age of majority" under FERPA), those
rights vest in the student, and the parent loses statutory access.

School officials with a legitimate educational interest retain access at
all ages, independent of the age-of-majority transition.

The wrinkle: Cedar's `duration` constructor accepts only string literals,
so the 18-year threshold must be hand-encoded as a conservative day count
that survives leap years. Using the same convention as
`age_verification_leap_years`, **18 years = 6575 days** (18*365 + 5
worst-case leap days). A student is "at least 18" when
`context.now.durationSince(principal.dateOfBirth) >= duration("6575d")`.

## Entities

- `Person` with attributes:
  - `dateOfBirth: datetime`
  - `relationshipToStudent: String` -- one of `"self"`, `"parent"`,
    `"guardian"`, `"school_official"`. (`"self"` means the principal is
    accessing their own record; the policy enforces that
    `principal == resource.studentId` in addition to the role.)
- `EducationalRecord` with:
  - `studentId: Person` -- the student to whom the record pertains.

## Actions

- `viewRecord` -- inspect the record contents.
- `requestCorrection` -- file a request to amend the record.
- `disclose` -- release the record to a third party.

Context for all actions: `now: datetime`.

## Requirements

### 1. viewRecord (Permit)

A `Person` may `viewRecord` on an `EducationalRecord` if any of:

- **Student themselves (any age):** `principal == resource.studentId`
  AND `principal.relationshipToStudent == "self"`. (No age gate -- the
  student may always see their own record. Schools that wish to gate
  minor self-access do so out-of-band.)
- **Parent of a minor student:** `principal.relationshipToStudent == "parent"`
  AND the *student* is **under 18**, i.e.
  `context.now.durationSince(resource.studentId.dateOfBirth) < duration("6575d")`.
- **Guardian of a minor student:** `principal.relationshipToStudent == "guardian"`
  AND the student is under 18 (same condition as parent).
- **School official (any age):** `principal.relationshipToStudent == "school_official"`.
  (FERPA's "legitimate educational interest" exception. The host
  application is assumed to have already verified the official's
  legitimate interest before the request reaches Cedar.)

### 2. requestCorrection (Permit)

Same access rules as `viewRecord`. The right to inspect and the right to
request amendment are paired under FERPA; both transfer at age 18.

### 3. disclose (Permit)

`disclose` is the act of *releasing* the record to a third party. Only a
`school_official` may perform `disclose`. Parents, guardians, and the
student themselves cannot use this action -- third-party disclosure is a
school-mediated act, not a self-service one. (The student's own
inspection / correction rights are covered by `viewRecord` and
`requestCorrection`.)

### 4. Floors

- A `school_official` MUST be permitted to `viewRecord` on any
  `EducationalRecord`, regardless of student age.
- A `school_official` MUST be permitted to `requestCorrection` on any
  `EducationalRecord`, regardless of student age.
- A `school_official` MUST be permitted to `disclose` any
  `EducationalRecord`.
- A `parent` MUST be permitted to `viewRecord` when the student is
  strictly under 18 (i.e.
  `context.now.durationSince(resource.studentId.dateOfBirth) < duration("6575d")`).
- A student themselves (`principal == resource.studentId` AND
  `principal.relationshipToStudent == "self"`) MUST be permitted to
  `viewRecord` on their own record.

## Notes

- The age-of-majority logic is intentionally encoded as a positive permit
  conditioned on `< 6575d`, **not** as a `forbid when ... >= 6575d`. Per
  CLAUDE.md §8.6 (role-intersection trap), a forbid keyed on
  `relationshipToStudent == "parent"` plus an age threshold could
  over-block: e.g., a person who is both the student's parent AND a
  school official would be forbidden by the negative rule despite having
  a separate legitimate-interest basis. Using positive permits that
  enumerate each valid grant lets the bounds compose cleanly.
- Cedar denies by default, so an over-18 student's parent simply receives
  no permit and is denied -- no explicit forbid required.
- The day threshold (6575d) deliberately matches the convention in
  `age_verification_leap_years`. A student with `dateOfBirth` exactly
  6575 days before `now` is considered "18 or older" and parental
  access is revoked.
- All datetime arithmetic uses `durationSince` returning a duration
  comparable to `duration("6575d")` (Go-style literal, per §8.9).
