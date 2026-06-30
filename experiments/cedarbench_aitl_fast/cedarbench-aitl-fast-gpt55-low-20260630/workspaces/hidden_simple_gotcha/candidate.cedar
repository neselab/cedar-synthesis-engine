permit (
    principal is User,
    action == Action::"read",
    resource is File
)
when {
    principal == resource.currentOwner ||
    principal == resource.creator
};

permit (
    principal is User,
    action == Action::"transfer",
    resource is File
)
when {
    principal == resource.currentOwner
};