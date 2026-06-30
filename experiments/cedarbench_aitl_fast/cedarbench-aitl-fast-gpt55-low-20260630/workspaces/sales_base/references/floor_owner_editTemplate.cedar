permit (
    principal is User,
    action == Action::"editTemplate",
    resource is Template
) when {
    principal == resource.owner
};