permit (
    principal is User,
    action == Action::"editTemplate",
    resource is Template
) when {
    resource.owner == principal &&
    principal.job == Job::"internal"
};