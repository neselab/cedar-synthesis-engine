// Floor: a teacher in the same class MUST be permitted to publishGrade.
permit (
    principal is User,
    action == Action::"publishGrade",
    resource is GradeRecord
)
when {
    principal.role == "teacher"
    && principal.assignedClass == resource.class
};
