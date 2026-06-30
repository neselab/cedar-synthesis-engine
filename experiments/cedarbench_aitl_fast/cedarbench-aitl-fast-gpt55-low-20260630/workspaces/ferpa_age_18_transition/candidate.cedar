permit (
    principal,
    action == Action::"viewRecord",
    resource
)
when {
    principal is Person &&
    resource is EducationalRecord &&
    principal == resource.studentId &&
    principal.relationshipToStudent == "self"
};

permit (
    principal,
    action == Action::"viewRecord",
    resource
)
when {
    principal is Person &&
    resource is EducationalRecord &&
    principal.relationshipToStudent == "parent" &&
    context.now.durationSince(resource.studentId.dateOfBirth) < duration("6575d")
};

permit (
    principal,
    action == Action::"viewRecord",
    resource
)
when {
    principal is Person &&
    resource is EducationalRecord &&
    principal.relationshipToStudent == "guardian" &&
    context.now.durationSince(resource.studentId.dateOfBirth) < duration("6575d")
};

permit (
    principal,
    action == Action::"viewRecord",
    resource
)
when {
    principal is Person &&
    resource is EducationalRecord &&
    principal.relationshipToStudent == "school_official"
};

permit (
    principal,
    action == Action::"requestCorrection",
    resource
)
when {
    principal is Person &&
    resource is EducationalRecord &&
    principal == resource.studentId &&
    principal.relationshipToStudent == "self"
};

permit (
    principal,
    action == Action::"requestCorrection",
    resource
)
when {
    principal is Person &&
    resource is EducationalRecord &&
    principal.relationshipToStudent == "parent" &&
    context.now.durationSince(resource.studentId.dateOfBirth) < duration("6575d")
};

permit (
    principal,
    action == Action::"requestCorrection",
    resource
)
when {
    principal is Person &&
    resource is EducationalRecord &&
    principal.relationshipToStudent == "guardian" &&
    context.now.durationSince(resource.studentId.dateOfBirth) < duration("6575d")
};

permit (
    principal,
    action == Action::"requestCorrection",
    resource
)
when {
    principal is Person &&
    resource is EducationalRecord &&
    principal.relationshipToStudent == "school_official"
};

permit (
    principal,
    action == Action::"disclose",
    resource
)
when {
    principal is Person &&
    resource is EducationalRecord &&
    principal.relationshipToStudent == "school_official"
};