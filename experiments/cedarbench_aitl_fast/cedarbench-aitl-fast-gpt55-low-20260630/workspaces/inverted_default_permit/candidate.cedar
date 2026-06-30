permit (
    principal is User,
    action == Action::"read",
    resource is PublicArticle
)
when {
    !resource.bannedReaders.contains(principal.id)
};