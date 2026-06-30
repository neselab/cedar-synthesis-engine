// Floor: a school official MUST be permitted to requestCorrection on
// any EducationalRecord, regardless of student age.
permit (
    principal is Person,
    action == Action::"requestCorrection",
    resource is EducationalRecord
)
when {
    principal.relationshipToStudent == "school_official"
};
