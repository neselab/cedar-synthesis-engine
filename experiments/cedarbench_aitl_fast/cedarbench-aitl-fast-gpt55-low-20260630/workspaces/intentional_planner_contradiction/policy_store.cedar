// Policy store — verified policies appended here

// --- Verified (eval iteration 1) ---
permit (
    principal is User,
    action == Action::"readPost",
    resource is Post
);

forbid (
    principal is User,
    action == Action::"readPost",
    resource is Post
)
when {
    principal in resource.author.blocked ||
    resource.author in principal.blocked
};
