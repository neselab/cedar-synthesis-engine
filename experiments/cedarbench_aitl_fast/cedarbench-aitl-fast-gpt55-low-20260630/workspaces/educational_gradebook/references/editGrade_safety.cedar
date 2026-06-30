// Ceiling: editGrade permitted only when teacher in same class AND
// grade is not yet finalized.
permit (
    principal is User,
    action == Action::"editGrade",
    resource is GradeRecord
)
when {
    principal.role == "teacher"
    && principal.assignedClass == resource.class
    && resource.isFinal == false
};
