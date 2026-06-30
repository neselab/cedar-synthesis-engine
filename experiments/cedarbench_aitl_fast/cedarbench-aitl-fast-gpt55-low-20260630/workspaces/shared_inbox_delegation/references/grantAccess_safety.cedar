// Ceiling: grantAccess permitted only when principal is the owner.
permit (
    principal is User,
    action == Action::"grantAccess",
    resource is Mailbox
)
when {
    principal == resource.owner
};
