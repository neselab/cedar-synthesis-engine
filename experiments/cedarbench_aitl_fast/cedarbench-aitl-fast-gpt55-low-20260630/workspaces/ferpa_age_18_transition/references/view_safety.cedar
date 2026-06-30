// Ceiling: viewRecord permitted only for an enumerated set of
// principals against the per-record student. Encodes the FERPA
// age-of-majority transition: parent/guardian permits require the
// student to be strictly under 18 (6575 days = 18*365 + 5 worst-case
// leap days). School officials and the student themselves get access
// independent of age.
permit (
    principal is Person,
    action == Action::"viewRecord",
    resource is EducationalRecord
)
when {
    (principal == resource.studentId
     && principal.relationshipToStudent == "self")
    || (principal.relationshipToStudent == "parent"
        && context.now.durationSince(resource.studentId.dateOfBirth) < duration("6575d"))
    || (principal.relationshipToStudent == "guardian"
        && context.now.durationSince(resource.studentId.dateOfBirth) < duration("6575d"))
    || principal.relationshipToStudent == "school_official"
};
