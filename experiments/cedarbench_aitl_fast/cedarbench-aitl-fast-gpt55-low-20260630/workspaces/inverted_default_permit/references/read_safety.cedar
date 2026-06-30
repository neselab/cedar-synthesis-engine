// Ceiling: read is permitted exactly when the user's id is NOT in the
// article's bannedReaders set. PublicArticles are public-by-default;
// the only gate is the explicit denylist.
permit (
    principal is User,
    action == Action::"read",
    resource is PublicArticle
)
when {
    !(resource.bannedReaders.contains(principal.id))
};
