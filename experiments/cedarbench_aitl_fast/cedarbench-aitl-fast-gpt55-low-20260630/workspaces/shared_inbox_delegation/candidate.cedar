permit (
    principal is User,
    action == Action::"readMail",
    resource is Mailbox
)
when {
    principal == resource.owner ||
    resource.delegates.contains(principal) ||
    resource.members.contains(principal)
};

permit (
    principal is User,
    action == Action::"sendAs",
    resource is Mailbox
)
when {
    principal == resource.owner ||
    resource.delegates.contains(principal)
};

permit (
    principal is User,
    action == Action::"manageFolders",
    resource is Mailbox
)
when {
    principal == resource.owner
};

permit (
    principal is User,
    action == Action::"grantAccess",
    resource is Mailbox
)
when {
    principal == resource.owner
};