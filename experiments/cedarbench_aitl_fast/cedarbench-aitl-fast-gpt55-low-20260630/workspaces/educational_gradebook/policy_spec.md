---
pattern: educational gradebook access
difficulty: medium
features:
  - role-based access (teacher, student, parent)
  - class-scoped visibility
  - optional context attribute with has-guarding
  - boolean attribute gating (isFinal)
  - self-access pattern (principal == resource.studentId)
domain: education
synthesis_difficulty: 3
---

# Educational Gradebook Access Control

## Context

This policy governs visibility and modification of academic grade records
in a school's learning management system. Three roles interact with
grades: **teachers** who assign and publish grades, **students** who view
their own grades, and **parents** who view their child's grades.

Every `User` has a `role` (one of `"teacher"`, `"student"`, `"parent"`)
and an `assignedClass` identifying the class section they belong to.
Every `GradeRecord` belongs to a specific student (`studentId: User`),
a class section (`class: String`), and has a finality flag (`isFinal:
Bool`).

The request context carries an optional `parentOf` attribute of type
`User`, present only when the principal is a parent. The host
application pre-validates the parent-child relationship and attaches it
to the request context. When `parentOf` is absent, the parent-access
path is unavailable.

Four actions: `viewGrade`, `editGrade`, `publishGrade`,
`viewClassAverage`.

## Requirements

### 1. View Grade (Permit)

A User may `viewGrade` on a `GradeRecord` in any of these cases:

- **Teacher in same class:** `principal.role == "teacher"` AND
  `principal.assignedClass == resource.class`.
- **Student self-access:** `principal.role == "student"` AND
  `principal == resource.studentId` (the student is viewing their own
  grade).
- **Parent of the student:** `principal.role == "parent"` AND
  `context.parentOf` is present AND `context.parentOf == resource.studentId`
  (the parent is viewing the grade of their linked child).

No other combinations are permitted for `viewGrade`.

### 2. Edit Grade (Permit)

A User may `editGrade` on a `GradeRecord` only when ALL of:

- `principal.role == "teacher"`, AND
- `principal.assignedClass == resource.class` (same class), AND
- `resource.isFinal == false` (grade has not yet been finalized).

Students and parents may never edit grades. Teachers may not edit
finalized grades.

### 3. Publish Grade (Permit)

A User may `publishGrade` on a `GradeRecord` only when:

- `principal.role == "teacher"`, AND
- `principal.assignedClass == resource.class` (same class).

Publishing marks the grade as final. Only teachers in the same class
may publish. There is no finality guard on publish (a teacher can
re-publish an already-final grade).

### 4. View Class Average (Permit)

A User may `viewClassAverage` on a `GradeRecord` when:

- `principal.role == "teacher"` AND `principal.assignedClass == resource.class`, OR
- `principal.role == "student"` AND `principal.assignedClass == resource.class`.

Parents may not view class averages. Only teachers and students in the
same class may view them.

## Notes

- Cedar denies by default, so the absence of a matching permit is
  sufficient to block unauthorized access. No explicit forbid rules
  are required (though defensive forbids are acceptable).
- The `parentOf` context attribute is optional (`parentOf?: User`).
  Policies MUST guard access with `context has parentOf` before reading
  `context.parentOf`. Failure to do so will cause Cedar type-check
  errors.
- The `isFinal` flag on `GradeRecord` gates only `editGrade`, not
  `viewGrade` or `publishGrade`.
- Common pitfalls: forgetting the `has` guard on `parentOf`, allowing
  parents to edit grades, allowing cross-class teacher access, or
  forgetting the finality check on edit.
