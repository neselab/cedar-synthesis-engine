permit (
    principal is User,
    action == Action::"viewTemplate",
    resource is Template
) when {
    resource.owner == principal
};