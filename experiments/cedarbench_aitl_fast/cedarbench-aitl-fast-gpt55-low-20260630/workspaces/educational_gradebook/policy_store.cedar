// Policy store — verified policies appended here

// --- Verified (eval iteration 1) ---
permit (
    principal is User,
    action == Action::"viewGrade",
    resource is GradeRecord
)
when {
    principal.role == "teacher" &&
    principal.assignedClass == resource.class
};

permit (
    principal is User,
    action == Action::"viewGrade",
    resource is GradeRecord
)
when {
    principal.role == "student" &&
    principal == resource.studentId
};

permit (
    principal is User,
    action == Action::"viewGrade",
    resource is GradeRecord
)
when {
    principal.role == "parent" &&
    context has parentOf &&
    context.parentOf == resource.studentId
};

permit (
    principal is User,
    action == Action::"editGrade",
    resource is GradeRecord
)
when {
    principal.role == "teacher" &&
    principal.assignedClass == resource.class &&
    resource.isFinal == false
};

permit (
    principal is User,
    action == Action::"publishGrade",
    resource is GradeRecord
)
when {
    principal.role == "teacher" &&
    principal.assignedClass == resource.class
};

permit (
    principal is User,
    action == Action::"viewClassAverage",
    resource is GradeRecord
)
when {
    principal.role == "teacher" &&
    principal.assignedClass == resource.class
};

permit (
    principal is User,
    action == Action::"viewClassAverage",
    resource is GradeRecord
)
when {
    principal.role == "student" &&
    principal.assignedClass == resource.class
};
