permit (
    principal is User,
    action == Action::"view",
    resource is Document
)
when {
    principal in [Group::"admins", Group::"auditors", Group::"compliance"] ||
    resource.owner in [Group::"admins", Group::"auditors", Group::"compliance"] ||
    principal == resource.owner
};

permit (
    principal is User,
    action == Action::"share",
    resource is Document
)
when {
    (resource.members.contains(principal) || principal == resource.owner) &&
    resource.aliases.containsAny(["share-allowed", "public"])
};