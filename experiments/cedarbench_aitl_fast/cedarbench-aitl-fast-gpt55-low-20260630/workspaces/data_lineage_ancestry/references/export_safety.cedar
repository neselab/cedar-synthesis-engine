// Ceiling: export permitted only when clearance dominates classification
// AND the dataset does not contain personal data.
permit (
    principal is User,
    action == Action::"export",
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
    && !resource.hasPersonalData
};
