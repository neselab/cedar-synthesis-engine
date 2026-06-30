// Floor: a teacher in the same class MUST be permitted to editGrade
// when the grade is not finalized.
permit (
    principal is User,
    action == Action::"editGrade",
    resource is GradeRecord
)
when {
    principal.role == "teacher"
    && principal.assignedClass == resource.class
    && resource.isFinal == false
};
