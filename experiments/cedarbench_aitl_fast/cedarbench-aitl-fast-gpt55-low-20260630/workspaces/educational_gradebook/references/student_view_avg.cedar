// Floor: a student in the same class MUST be permitted to
// viewClassAverage.
permit (
    principal is User,
    action == Action::"viewClassAverage",
    resource is GradeRecord
)
when {
    principal.role == "student"
    && principal.assignedClass == resource.class
};
