permit (
    principal is User,
    action in Action::"Role-A Actions",
    resource is Workspace
)
when {
    principal in Role::"Role-A"
};

permit (
    principal is User,
    action == Action::"ReadWorkspace",
    resource is Workspace
)
when {
    principal in Role::"Role-B" ||
    principal == resource.owner
};
