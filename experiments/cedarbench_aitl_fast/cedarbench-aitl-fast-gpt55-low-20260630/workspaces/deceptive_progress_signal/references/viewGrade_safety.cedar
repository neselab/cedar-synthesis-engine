// Ceiling: viewGrade permitted ONLY when one of:
//   - teacher (any dept)
//   - TA in same subject as exam
//   - student viewing own exam
permit (
    principal is User,
    action == Action::"viewGrade",
    resource is Exam
)
when {
    principal.role == "teacher"
    || (principal.role == "ta" && principal.dept == resource.subject)
    || (principal.role == "student" && principal == resource.student)
};
