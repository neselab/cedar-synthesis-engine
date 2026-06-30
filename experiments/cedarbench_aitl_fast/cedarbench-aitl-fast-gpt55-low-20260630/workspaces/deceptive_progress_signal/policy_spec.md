---
pattern: deceptive progress signal — near-symmetric 3x3 role/action matrix
difficulty: hard (planning)
features:
  - role-based access (teacher / ta / student)
  - subject-scoped gating with cross-action asymmetry
  - instructor-of-resource bypass on edit only
  - student self-access on view only
  - three actions with deceptively similar permission shapes
domain: education / exam grading
synthesis_difficulty: 4
---

# Deceptive Progress Signal — Exam Grading System

## Context

This scenario governs an exam-grading system with three user roles
(`teacher`, `ta`, `student`) and three actions (`viewGrade`,
`editGrade`, `addComment`). The 3x3 action-by-role matrix is
**near-symmetric**: each role has *almost* the same permissions across
the three actions, but with one subtly different subject-scope or
exclusion in each cell.

The design goal is to construct an oscillation trap: every "natural
fix" the synthesizer reaches for trades one violation for another. The
violation **count** drops (set-based progress signal looks like
progress), the candidate **hash** changes (no oscillation detected),
but the candidate is wrong in a different way.

This scenario is a deliberate stress test of:
- **§8.1 directional feedback** — only per-floor / per-ceiling
  attribution can localize each violation; bulk-counting is misled.
- **§8.2 set-based oscillation detection** — by construction, count
  monotonically decreases for several wrong steps.
- **§8.6 role-intersection trap** — `forbid when principal.role == "ta"`
  on `editGrade` would also fire when the same TA happens to also be
  the instructor of the exam (instructor bypass on edit).

## Domain model

- **User:** `role: String` (one of `"teacher"`, `"ta"`, `"student"`),
  `dept: String` (one of `"math"`, `"cs"`, `"eng"`).
- **Exam:** `subject: String` (one of `"math"`, `"cs"`, `"eng"`),
  `instructor: User` (the exam's owning instructor — typically a
  teacher, but the schema does not enforce this), `student: User`
  (the student whose grade this exam record represents).
- **Actions:** `viewGrade`, `editGrade`, `addComment`.

"In own subject" means `principal.dept == resource.subject`. Equality
of strings is the matching predicate (NOT pattern matching).

## Requirements — the 3x3 matrix

For each (action, role) cell below, the rule is **exact**: the
listed conditions are necessary AND sufficient. No other permit paths.

### viewGrade

| Role     | Permit when                                                      |
|----------|------------------------------------------------------------------|
| teacher  | always (any teacher in any dept may view any exam)               |
| ta       | `principal.dept == resource.subject` (TA in own subject only)    |
| student  | `principal == resource.student` (student viewing own exam only)  |

**Trap:** the unscoped teacher permit invites the synthesizer to add
an unscoped TA permit (`permit when principal.role == "ta"`), but
that breaks the ceiling — TAs may not view exams outside their
subject.

### editGrade

| Role     | Permit when                                                       |
|----------|-------------------------------------------------------------------|
| teacher  | `principal.dept == resource.subject` (teacher in same subject)    |
| ta       | NEVER — TAs may not edit, even in their own subject               |
| student  | NEVER — students may not edit                                     |
| (any)    | `principal == resource.instructor` (instructor bypass; any role)  |

**Traps:**
- The teacher rule for `editGrade` is **subject-scoped** unlike the
  teacher rule for `viewGrade` (which is unscoped). A synthesizer
  that copy-pastes the `viewGrade` teacher permit into `editGrade`
  satisfies the floor but breaks the ceiling.
- Adding `forbid when principal.role == "ta"` on `editGrade`
  satisfies the "TAs cannot edit" ceiling clause but breaks the
  instructor-bypass floor when a TA is the listed instructor (§8.6
  role-intersection trap).

### addComment

| Role     | Permit when                                                       |
|----------|-------------------------------------------------------------------|
| teacher  | `principal.dept == resource.subject` (teacher in same subject)    |
| ta       | `principal.dept == resource.subject` (TA in same subject)         |
| student  | NEVER — students may not comment                                  |

**Trap:** the natural "fix" of removing the subject restriction from
the `viewGrade` TA permit (to satisfy a "TA can view any exam"
floor that doesn't actually exist) is plausible because the **teacher**
viewGrade rule is unscoped — but TAs are not teachers, and removing
the subject restriction breaks the ceiling.

Symmetrically, the natural fix of adding `permit when role == "ta"` to
`viewGrade` (to fix a "TA can view exam in own subject" floor) ALSO
"would make sense" to apply to `addComment` — but `addComment`
already requires the subject scope, so the unscoped permit breaks the
addComment ceiling.

## Why this oscillates (planner's note)

The 3x3 matrix has nine cells. Each role/action pair is in one of three
states: **always permit**, **subject-scoped permit**, or **never
permit**. The permitted/forbidden distribution looks symmetric across
the diagonal but is not — for example:

- `viewGrade × teacher` = always permit (no scope)
- `editGrade × teacher` = subject-scoped permit
- `addComment × teacher` = subject-scoped permit

A synthesizer that tries to "unify" the teacher rules by giving
teachers an unscoped permit on all three actions would satisfy three
floors but break two ceilings (editGrade and addComment).

Each "fix" trades violations:
1. Adding unscoped TA viewGrade: fixes 1 floor, breaks 1 ceiling.
2. Adding unscoped teacher editGrade: fixes 1 floor, breaks 1 ceiling.
3. `forbid when role == "ta"` on editGrade: fixes 1 ceiling, breaks 1 floor.
4. Removing subject scope from addComment TA permit: fixes 0 floors
   (it's already correct), breaks 1 ceiling.

Each step keeps the violation **count** plausibly low while the
candidate is genuinely different (defeats hash-based dedup).

The intended converged candidate has nine narrowly-scoped permit
clauses (one per non-NEVER cell), with the instructor-bypass on
editGrade as a separate disjunct. No global forbids. The synthesizer
can only reach this with **per-violation directional feedback** that
distinguishes "the editGrade ceiling broke in cell (teacher, wrong
subject)" from "the viewGrade floor broke in cell (TA, own subject)".

## Notes

- Cedar denies by default; floors below are intentionally minimal
  (one floor per non-NEVER cell that has a non-trivial requirement).
- All "in own subject" matching is string equality
  (`principal.dept == resource.subject`), not pattern matching.
- The `instructor` field on `Exam` is a `User`, not constrained to
  any specific role. The instructor-bypass on `editGrade` applies
  regardless of the instructor's role string.
- `principal == resource.student` is the student self-access predicate
  for `viewGrade`. There is no "parent" role and no parent-child
  context in this scenario.
