// Ceiling: viewClassAverage permitted only when teacher in same class
// OR student in same class.
permit (
    principal is User,
    action == Action::"viewClassAverage",
    resource is GradeRecord
)
when {
    (principal.role == "teacher" && principal.assignedClass == resource.class)
    || (principal.role == "student" && principal.assignedClass == resource.class)
};
