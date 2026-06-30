permit (
    principal is User,
    action == Action::"query",
    resource is Dataset
)
when {
    resource.classification == "public" ||
    (resource.classification == "internal" &&
        (principal.clearance == "internal" || principal.clearance == "restricted")) ||
    (resource.classification == "restricted" &&
        principal.clearance == "restricted")
};

permit (
    principal is User,
    action == Action::"derive",
    resource is Dataset
)
when {
    principal.department == resource.sourceDepartment &&
    (
        resource.classification == "public" ||
        (resource.classification == "internal" &&
            (principal.clearance == "internal" || principal.clearance == "restricted")) ||
        (resource.classification == "restricted" &&
            principal.clearance == "restricted")
    )
};

permit (
    principal is User,
    action == Action::"export",
    resource is Dataset
)
when {
    resource.hasPersonalData == false &&
    (
        resource.classification == "public" ||
        (resource.classification == "internal" &&
            (principal.clearance == "internal" || principal.clearance == "restricted")) ||
        (resource.classification == "restricted" &&
            principal.clearance == "restricted")
    )
};

permit (
    principal is User,
    action == Action::"delete",
    resource is Dataset
)
when {
    principal.clearance == "restricted" &&
    principal.department == resource.sourceDepartment
};