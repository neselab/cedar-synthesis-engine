// Floor: a parent of a student who is strictly under 18 (i.e. fewer
// than 6575 days have elapsed since the student's date of birth as of
// context.now) MUST be permitted to viewRecord on that student's
// EducationalRecord. This is the parental-rights side of the FERPA
// age-of-majority transition.
permit (
    principal is Person,
    action == Action::"viewRecord",
    resource is EducationalRecord
)
when {
    principal.relationshipToStudent == "parent"
    && context.now.durationSince(resource.studentId.dateOfBirth) < duration("6575d")
};
