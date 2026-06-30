// Floor: when the article's bannedReaders set is empty, any user MUST be
// permitted to read. This anchors the "no one banned" subcase explicitly,
// catching candidates that require some additional positive condition
// (auth check, role, group membership) the spec does not allow.
permit (
    principal is User,
    action == Action::"read",
    resource is PublicArticle
)
when {
    resource.bannedReaders.isEmpty()
};
