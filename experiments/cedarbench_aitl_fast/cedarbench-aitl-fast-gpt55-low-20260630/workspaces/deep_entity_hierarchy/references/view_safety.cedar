// Ceiling: view is permitted only when classification is public/internal
// (any employee) OR classification is confidential AND same team.
permit (
    principal is Employee,
    action == Action::"view",
    resource is Document
)
when {
    resource.classification == "public"
    || resource.classification == "internal"
    || (resource.classification == "confidential" && principal in resource.ownerTeam)
};
