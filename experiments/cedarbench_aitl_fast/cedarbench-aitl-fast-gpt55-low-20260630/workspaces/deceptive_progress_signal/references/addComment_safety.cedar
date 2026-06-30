// Ceiling: addComment permitted ONLY when one of:
//   - teacher in same subject as exam
//   - TA in same subject as exam
// Students NEVER permitted.
permit (
    principal is User,
    action == Action::"addComment",
    resource is Exam
)
when {
    ((principal.role == "teacher" || principal.role == "ta")
     && principal.dept == resource.subject)
};
