// Ceiling: manageFolders permitted only when principal is the owner.
permit (
    principal is User,
    action == Action::"manageFolders",
    resource is Mailbox
)
when {
    principal == resource.owner
};
