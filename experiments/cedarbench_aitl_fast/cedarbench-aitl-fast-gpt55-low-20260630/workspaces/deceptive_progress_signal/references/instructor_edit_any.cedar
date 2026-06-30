// Floor: the listed instructor on an exam MUST be permitted to
// editGrade, regardless of their role string. This is the
// instructor-bypass — it applies even if the instructor's role is
// "ta" or "student" (an edge case the schema permits even if the
// product domain discourages it).
//
// §8.6 trap: a `forbid when principal.role == "ta"` on editGrade
// would break this floor when a TA happens to be the instructor.
permit (
    principal is User,
    action == Action::"editGrade",
    resource is Exam
)
when {
    principal == resource.instructor
};
