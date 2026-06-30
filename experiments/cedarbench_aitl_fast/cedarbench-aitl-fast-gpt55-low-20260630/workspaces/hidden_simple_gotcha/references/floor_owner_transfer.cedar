// Floor: the current owner MUST be able to transfer the file.
permit (
    principal is User,
    action == Action::"transfer",
    resource is File
)
when {
    principal == resource.currentOwner
};
