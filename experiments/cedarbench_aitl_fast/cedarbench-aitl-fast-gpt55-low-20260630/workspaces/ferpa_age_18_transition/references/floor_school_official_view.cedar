// Floor: a school official MUST be permitted to viewRecord on any
// EducationalRecord, regardless of student age (FERPA "legitimate
// educational interest" exception).
permit (
    principal is Person,
    action == Action::"viewRecord",
    resource is EducationalRecord
)
when {
    principal.relationshipToStudent == "school_official"
};
