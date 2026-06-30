// Floor: a TA whose dept matches the exam subject MUST be permitted
// to viewGrade. TAs in other subjects are NOT covered by this floor
// (and the ceiling forbids them).
permit (
    principal is User,
    action == Action::"viewGrade",
    resource is Exam
)
when {
    principal.role == "ta"
    && principal.dept == resource.subject
};
