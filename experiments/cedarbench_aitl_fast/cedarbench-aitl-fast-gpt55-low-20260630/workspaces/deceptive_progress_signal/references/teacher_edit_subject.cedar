// Floor: a teacher whose dept matches the exam subject MUST be
// permitted to editGrade. Teachers in other subjects are NOT covered
// by this floor (and the ceiling forbids them on editGrade — note the
// asymmetry vs viewGrade where teachers are unscoped).
permit (
    principal is User,
    action == Action::"editGrade",
    resource is Exam
)
when {
    principal.role == "teacher"
    && principal.dept == resource.subject
};
