---
pattern: ITAR / EAR export control / US-persons-only / deemed export
difficulty: medium
features:
  - string-enum citizenship status (single-valued, not Set)
  - context-based location check (deemed export)
  - action variants with progressively stricter requirements
  - controlled-versus-uncontrolled data dichotomy
domain: aerospace, defense, dual-use technology
synthesis_difficulty: 3
---

# ITAR / EAR US-Persons-Only — Policy Specification

## Context

This policy implements US export-control rules under the International
Traffic in Arms Regulations (ITAR, 22 CFR 120-130) and the Export
Administration Regulations (EAR, 15 CFR 730-774). Both regulatory
regimes restrict access to controlled "technical data" by foreign
nationals — even within the United States — under the **deemed export**
doctrine: a release of technical data to a foreign person is treated
as an export to that person's country of nationality.

Two regulatory facts are encoded:
1. ITAR-controlled data (USML — defense articles) may be released
   only to "US persons" (US citizens and Lawful Permanent Residents).
2. EAR-controlled data above the catch-all EAR99 category is similarly
   restricted, with a partial carve-out for engineers visiting from
   non-embargoed countries (kept narrow here for tractability).

Principal is `Engineer`; resource is `TechnicalData`. Three actions
of increasing strictness: `view`, `download`, `export`.

## Citizenship Status

Each `Engineer` carries a `citizenshipStatus` string with exactly four
values:

| Value         | Meaning                                                |
|---------------|--------------------------------------------------------|
| `US_CITIZEN`  | US citizen — "US person" under 22 CFR 120.62.          |
| `LPR`         | Lawful Permanent Resident — "US person".               |
| `VISA`        | Foreign national present on a US visa (H-1B, F-1, …).  |
| `NON_US`      | Foreign national not present in the US.                |

A "US person" means `citizenshipStatus == "US_CITIZEN"` or
`citizenshipStatus == "LPR"`. This is a **single-valued string field**,
not a `Set<String>` — every engineer has exactly one status.

## Data Classification

Each `TechnicalData` resource carries:
- `itarControlled: Bool` — true iff the data is on the US Munitions List.
- `earCategory: String` — `"EAR99"` for the public/uncontrolled
  catch-all category, or a controlled ECCN string (e.g. `"5A002"`,
  `"3A001"`) for items controlled under the EAR's Commerce Control List.

A datum is "uncontrolled" iff `itarControlled == false &&
earCategory == "EAR99"`. Anything else is "controlled."

## Requirements

### 1. `view`

A US person (`US_CITIZEN` or `LPR`) may always view, regardless of
classification or location.

A non-US person (`VISA` or `NON_US`) may view only if the data is
*uncontrolled* — that is, both `itarControlled == false` and
`earCategory == "EAR99"`.

ITAR-controlled data: only US persons may view.
EAR-controlled-above-EAR99: only US persons may view.
EAR99 + not ITAR: anyone may view.

### 2. `download`

Same rules as `view`, **plus** the deemed-export location check:
downloading ITAR-controlled data requires `accessLocation == "US"`,
even for US persons. A US citizen who downloads ITAR data while
physically located abroad is treated as having exported the data to
that country.

For non-ITAR data, no location restriction on download — a US person
may download EAR99 or EAR-controlled data from any location, and a
non-US person may download EAR99 data from any location.

### 3. `export`

The strictest action. An engineer may `export` only when ALL of:
- `citizenshipStatus == "US_CITIZEN"` or `"LPR"` (US person),
- `clearanceVerified == true` (export-control briefing on file),
- `accessLocation == "US"` (deemed-export rule).

The `export` action is restricted regardless of whether the data is
ITAR, EAR-controlled, or EAR99 — exporting any data is a deliberate,
gated action.

## Notes / Failure Modes

- **§8.6 Role-intersection trap.** Do NOT encode "non-US persons can't
  view ITAR data" as a global `forbid when principal.citizenshipStatus
  == "NON_US"` style rule. The `citizenshipStatus` field is single-
  valued, so this particular shape doesn't have the multi-role bug
  here, but a forbid like `forbid when citizenshipStatus != "US_CITIZEN"
  && citizenshipStatus != "LPR"` would still block legitimate viewing
  of EAR99 data by non-US persons. Use positive permits and let
  Cedar's default-deny do the rest.

- **US-person predicate.** The check is exactly
  `(principal.citizenshipStatus == "US_CITIZEN" ||
    principal.citizenshipStatus == "LPR")`.
  Cedar has no enum ordering and no `in` against a literal set of
  strings, so the disjunction is the canonical encoding.

- **Deemed export.** The location check applies even to US citizens
  for download/export of ITAR data. This is a real ITAR rule, not a
  modeling artifact.

- **Liveness.** Three liveness checks (one per action). Together with
  positive coverage for each action, these guarantee that the
  synthesized policy is not vacuously deny-all.
