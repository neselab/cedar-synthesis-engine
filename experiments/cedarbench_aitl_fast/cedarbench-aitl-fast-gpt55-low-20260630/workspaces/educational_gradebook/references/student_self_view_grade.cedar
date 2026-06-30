// Floor: a student viewing their own grade MUST be permitted.
permit (
    principal is User,
    action == Action::"viewGrade",
    resource is GradeRecord
)
when {
    principal.role == "student"
    && principal == resource.studentId
};
