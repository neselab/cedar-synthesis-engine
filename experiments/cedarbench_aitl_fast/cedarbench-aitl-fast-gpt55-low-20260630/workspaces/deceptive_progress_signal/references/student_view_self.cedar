// Floor: a student MUST be permitted to viewGrade on their own exam
// (where principal == resource.student).
permit (
    principal is User,
    action == Action::"viewGrade",
    resource is Exam
)
when {
    principal.role == "student"
    && principal == resource.student
};
