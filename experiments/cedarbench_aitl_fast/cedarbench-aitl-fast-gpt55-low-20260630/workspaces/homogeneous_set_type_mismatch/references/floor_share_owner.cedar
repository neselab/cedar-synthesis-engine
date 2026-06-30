// Floor: the document owner with an allowlisted alias MUST be able to share.
permit (
    principal is User,
    action == Action::"share",
    resource is Document
)
when {
    principal == resource.owner
    && resource.aliases.containsAny(["share-allowed", "public"])
};
