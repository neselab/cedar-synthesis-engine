// Floor: a teacher in the same class MUST be permitted to
// viewClassAverage.
permit (
    principal is User,
    action == Action::"viewClassAverage",
    resource is GradeRecord
)
when {
    principal.role == "teacher"
    && principal.assignedClass == resource.class
};
