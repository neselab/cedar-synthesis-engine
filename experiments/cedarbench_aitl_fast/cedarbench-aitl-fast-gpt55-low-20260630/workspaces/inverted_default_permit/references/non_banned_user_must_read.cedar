// Floor: a user whose id is NOT in the bannedReaders set MUST be
// permitted to read. This is the core "public by default" guarantee --
// any candidate that fails to permit a non-banned reader is over-denying.
permit (
    principal is User,
    action == Action::"read",
    resource is PublicArticle
)
when {
    !(resource.bannedReaders.contains(principal.id))
};
