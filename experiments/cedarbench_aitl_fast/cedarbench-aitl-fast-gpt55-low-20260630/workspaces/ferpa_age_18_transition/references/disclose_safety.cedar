// Ceiling: disclose (third-party release) is restricted to school
// officials only. Parents, guardians, and the student themselves do
// not perform third-party disclosure -- that is a school-mediated act.
permit (
    principal is Person,
    action == Action::"disclose",
    resource is EducationalRecord
)
when {
    principal.relationshipToStudent == "school_official"
};
