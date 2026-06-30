// Floor: the mailbox owner MUST be able to manageFolders.
permit (
    principal is User,
    action == Action::"manageFolders",
    resource is Mailbox
)
when {
    principal == resource.owner
};
