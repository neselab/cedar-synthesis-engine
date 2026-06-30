// Floor: any teacher (any dept) MUST be permitted to viewGrade.
// Note: this floor is unscoped — viewGrade is the ONLY action where
// teachers get unscoped access. The asymmetry is deliberate.
permit (
    principal is User,
    action == Action::"viewGrade",
    resource is Exam
)
when {
    principal.role == "teacher"
};
