// Floor: the author MUST be permitted to read their own post UNLESS
// they have self-blocked. The `!(principal in principal.blocked)`
// clause is the §8.8 floor-bound consistency exclusion for the
// blocking forbid in the self-reference case (when principal ==
// resource.author, the two blocking conditions both collapse to
// `principal in principal.blocked`, so one exclusion is sufficient).
permit (
    principal is User,
    action == Action::"readPost",
    resource is Post
)
when {
    principal == resource.author
    && !(principal in principal.blocked)
};
