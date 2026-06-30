// Ceiling: derive permitted only when clearance dominates classification
// AND the user's department matches the dataset's source department.
permit (
    principal is User,
    action == Action::"derive",
    resource is Dataset
)
when {
    (
        resource.classification == "public"
        || (resource.classification == "internal"
            && (principal.clearance == "internal" || principal.clearance == "restricted"))
        || (resource.classification == "restricted"
            && principal.clearance == "restricted")
    )
    && principal.department == resource.sourceDepartment
};
