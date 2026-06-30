// Ceiling: publishGrade permitted only when teacher in same class.
permit (
    principal is User,
    action == Action::"publishGrade",
    resource is GradeRecord
)
when {
    principal.role == "teacher"
    && principal.assignedClass == resource.class
};
