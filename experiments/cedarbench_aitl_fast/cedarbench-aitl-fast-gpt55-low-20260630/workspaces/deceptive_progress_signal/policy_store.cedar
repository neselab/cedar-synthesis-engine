// Policy store — verified policies appended here

// --- Verified (eval iteration 1) ---
permit (
    principal is User,
    action == Action::"viewGrade",
    resource is Exam
)
when {
    principal.role == "teacher"
};

permit (
    principal is User,
    action == Action::"viewGrade",
    resource is Exam
)
when {
    principal.role == "ta" &&
    principal.dept == resource.subject
};

permit (
    principal is User,
    action == Action::"viewGrade",
    resource is Exam
)
when {
    principal.role == "student" &&
    principal == resource.student
};

permit (
    principal is User,
    action == Action::"editGrade",
    resource is Exam
)
when {
    principal.role == "teacher" &&
    principal.dept == resource.subject
};

permit (
    principal is User,
    action == Action::"editGrade",
    resource is Exam
)
when {
    principal == resource.instructor
};

permit (
    principal is User,
    action == Action::"addComment",
    resource is Exam
)
when {
    principal.role == "teacher" &&
    principal.dept == resource.subject
};

permit (
    principal is User,
    action == Action::"addComment",
    resource is Exam
)
when {
    principal.role == "ta" &&
    principal.dept == resource.subject
};
