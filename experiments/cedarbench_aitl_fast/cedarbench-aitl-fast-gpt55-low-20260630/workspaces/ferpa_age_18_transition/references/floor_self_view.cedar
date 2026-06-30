// Floor: a student accessing their own record MUST be permitted to
// viewRecord. The "self" relationship is the post-18 access path; we
// also require principal == resource.studentId so a different person
// claiming "self" cannot read someone else's record.
permit (
    principal is Person,
    action == Action::"viewRecord",
    resource is EducationalRecord
)
when {
    principal == resource.studentId
    && principal.relationshipToStudent == "self"
};
