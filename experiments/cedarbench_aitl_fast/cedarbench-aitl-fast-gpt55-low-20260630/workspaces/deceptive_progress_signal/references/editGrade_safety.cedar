// Ceiling: editGrade permitted ONLY when one of:
//   - teacher in same subject as exam
//   - principal is the listed instructor (any role)
// TAs and students get NO permit path other than instructor-bypass.
permit (
    principal is User,
    action == Action::"editGrade",
    resource is Exam
)
when {
    (principal.role == "teacher" && principal.dept == resource.subject)
    || principal == resource.instructor
};
