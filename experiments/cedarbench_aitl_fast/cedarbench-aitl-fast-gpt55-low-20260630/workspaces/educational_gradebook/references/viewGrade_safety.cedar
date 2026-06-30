// Ceiling: viewGrade permitted only when (teacher in same class)
// OR (student viewing own grade) OR (parent with valid parentOf link).
permit (
    principal is User,
    action == Action::"viewGrade",
    resource is GradeRecord
)
when {
    (principal.role == "teacher" && principal.assignedClass == resource.class)
    || (principal.role == "student" && principal == resource.studentId)
    || (principal.role == "parent" && context has parentOf && context.parentOf == resource.studentId)
};
