// Floor: a parent with a valid parentOf context attribute pointing to
// the grade's student MUST be permitted to viewGrade.
permit (
    principal is User,
    action == Action::"viewGrade",
    resource is GradeRecord
)
when {
    principal.role == "parent"
    && context has parentOf
    && context.parentOf == resource.studentId
};
