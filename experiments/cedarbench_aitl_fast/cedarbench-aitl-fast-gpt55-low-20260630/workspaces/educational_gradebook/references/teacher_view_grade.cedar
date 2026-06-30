// Floor: a teacher in the same class MUST be permitted to viewGrade.
permit (
    principal is User,
    action == Action::"viewGrade",
    resource is GradeRecord
)
when {
    principal.role == "teacher"
    && principal.assignedClass == resource.class
};
