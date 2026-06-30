// Floor: a principal in the document's members set, with an allowlisted
// alias, MUST be able to share.
permit (
    principal is User,
    action == Action::"share",
    resource is Document
)
when {
    resource.members.contains(principal)
    && resource.aliases.containsAny(["share-allowed", "public"])
};
