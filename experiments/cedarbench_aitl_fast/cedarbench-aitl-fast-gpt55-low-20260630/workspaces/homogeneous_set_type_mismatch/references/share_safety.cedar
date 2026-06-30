// Ceiling: share permitted only when principal is owner or in members,
// AND aliases overlap the allowlisted alias-tag strings.
permit (
    principal is User,
    action == Action::"share",
    resource is Document
)
when {
    (resource.members.contains(principal) || principal == resource.owner)
    && resource.aliases.containsAny(["share-allowed", "public"])
};
