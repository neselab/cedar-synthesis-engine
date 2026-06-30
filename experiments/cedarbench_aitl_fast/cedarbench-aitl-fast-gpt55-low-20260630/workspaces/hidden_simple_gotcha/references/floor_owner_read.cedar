// Floor: the current owner MUST be able to read the file.
permit (
    principal is User,
    action == Action::"read",
    resource is File
)
when {
    principal == resource.currentOwner
};
