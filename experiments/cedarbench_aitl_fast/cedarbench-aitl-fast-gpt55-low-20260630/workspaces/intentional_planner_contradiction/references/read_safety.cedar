// Ceiling: readPost is permitted only when NEITHER the post's author
// has blocked the principal NOR the principal has blocked the author.
// This is the global blocking forbid expressed as a ceiling condition.
// The author themselves is also subject to this check (the self-block
// corner case).
permit (
    principal is User,
    action == Action::"readPost",
    resource is Post
)
when {
    !(principal in resource.author.blocked)
    && !(resource.author in principal.blocked)
};
