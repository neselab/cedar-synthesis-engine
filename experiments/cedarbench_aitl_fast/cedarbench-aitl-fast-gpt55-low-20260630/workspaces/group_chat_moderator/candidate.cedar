permit (
    principal is User,
    action == Action::"read",
    resource is Channel
)
when {
    resource.members.contains(principal) &&
    resource.isArchived == false
};

permit (
    principal is User,
    action == Action::"post",
    resource is Channel
)
when {
    resource.members.contains(principal) &&
    resource.isArchived == false
};

permit (
    principal is User,
    action == Action::"deleteMessage",
    resource is Channel
)
when {
    principal == resource.owner ||
    resource.moderators.contains(principal)
};

permit (
    principal is User,
    action == Action::"pin",
    resource is Channel
)
when {
    principal == resource.owner ||
    resource.moderators.contains(principal)
};

permit (
    principal is User,
    action == Action::"archive",
    resource is Channel
)
when {
    principal == resource.owner
};