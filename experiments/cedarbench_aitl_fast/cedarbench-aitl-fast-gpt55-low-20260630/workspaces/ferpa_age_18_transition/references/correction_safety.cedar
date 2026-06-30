// Ceiling: requestCorrection mirrors viewRecord access exactly. Under
// FERPA the rights to inspect and to request amendment are paired and
// transfer together at the age of majority.
permit (
    principal is Person,
    action == Action::"requestCorrection",
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
