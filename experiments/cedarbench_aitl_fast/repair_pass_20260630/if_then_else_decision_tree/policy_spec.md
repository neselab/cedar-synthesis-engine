---
pattern: nested if-then-else expressions
difficulty: medium
features:
  - expression-level if-then-else
  - nested conditionals
  - severity tiers
  - category branching
domain: incident response / security operations
synthesis_difficulty: 3
---

# If-Then-Else Decision Tree -- Policy Specification

## Context

This policy governs an incident-response platform where security and
operations responders interact with `Incident` records. Responder
authority is calibrated by clearance level, and the access decision is
modelled as a **decision tree** keyed on incident `severity` (and, for
`respond`, also `category`). The point under test is that the
synthesizer uses Cedar's expression-level `if ... then ... else`
operator rather than desugaring it into chained `&&`/`||` clauses.

Entities:
- `Responder` with `clearanceLevel: Long` (1-5; higher is greater
  authority).
- `Incident` with `severity: Long` (1-10) and `category: String`
  (one of `"network"`, `"security"`, `"data"`).

Actions: `view`, `respond`, `escalate`, `closeIncident`.

## Cedar `if-then-else` (facts)

Cedar provides an **expression-level** ternary of the form
`if X then Y else Z`. It is an expression (not a statement) and may
appear anywhere a Bool-typed expression is expected, including inside
the body of a `when` clause. The branches must have the same type.
The construct nests:

```
if A then B
else if C then D
else E
```

is parsed as `if A then B else (if C then D else E)`. Most LLMs default
to desugaring this into `(A && B) || (!A && C && D) || (!A && !C && E)`,
which is logically equivalent but textually distinct. References below
are written using the `if-then-else` form.

## Requirements

### 1. View -- Severity-Tiered Clearance (Permit)

A `Responder` may `view` an `Incident` when their `clearanceLevel`
meets the threshold dictated by the incident's `severity`:

```
if   resource.severity >= 8 then principal.clearanceLevel >= 4
else if resource.severity >= 5 then principal.clearanceLevel >= 3
else if resource.severity >= 3 then principal.clearanceLevel >= 2
else                                principal.clearanceLevel >= 1
```

That is: severities 8-10 require clearance >= 4; severities 5-7
require >= 3; severities 3-4 require >= 2; severities 1-2 require
>= 1 (which is satisfied by every Responder).

### 2. Respond -- Severity AND Category Thresholds (Permit)

A `Responder` may `respond` to an `Incident` only when **both**
the severity-tiered threshold (from rule 1) AND the category-tiered
threshold are satisfied. The category-tiered threshold is:

```
if   resource.category == "security" then principal.clearanceLevel >= 4
else if resource.category == "data"  then principal.clearanceLevel >= 3
else                                       principal.clearanceLevel >= 2
```

(`"network"` falls into the final `else`, requiring >= 2.) Both
the severity rule and the category rule must hold for `respond` to
be permitted.

### 3. Escalate -- Severity-Gated (Permit)

A `Responder` may `escalate` an `Incident`:

- If `resource.severity < 8`, any `Responder` may escalate
  (no clearance requirement beyond being a `Responder`).
- If `resource.severity >= 8`, the `Responder` must have
  `clearanceLevel >= 4`.

In `if-then-else` form:

```
if resource.severity >= 8 then principal.clearanceLevel >= 4
else                            true
```

### 4. Close Incident -- Senior Only (Permit)

A `Responder` may `closeIncident` only when their `clearanceLevel`
is at least `5`. There is no severity- or category-conditional
relaxation of this bar.

## Notes

- `clearanceLevel` is a `Long` in the range 1-5. `severity` is a
  `Long` in the range 1-10. `category` is exactly one of `"network"`,
  `"security"`, or `"data"` -- no other values exist.
- Cedar denies by default; the absence of a permit is sufficient to
  deny. There are no `forbid` rules in this scenario.
- The references in `references/` are written using the `if-then-else`
  form. A candidate that desugars into `&&`/`||` is logically
  equivalent and will satisfy the verifier (the goal of the scenario
  is to demonstrate that the construct is available, not to require
  one specific syntax for correctness).
