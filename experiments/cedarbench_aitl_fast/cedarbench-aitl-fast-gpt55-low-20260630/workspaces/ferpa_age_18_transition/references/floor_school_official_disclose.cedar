// Floor: a school official MUST be permitted to disclose any
// EducationalRecord.
permit (
    principal is Person,
    action == Action::"disclose",
    resource is EducationalRecord
)
when {
    principal.relationshipToStudent == "school_official"
};
