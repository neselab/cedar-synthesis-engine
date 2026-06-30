// Policy store — verified policies appended here

// --- Verified (eval iteration 1) ---
permit (
    principal is Member,
    action == Action::"read",
    resource is Channel
) when {
    resource.members.contains(principal) ||
    (resource.isPublic && principal.hasAccess)
};

permit (
    principal is Member,
    action == Action::"post",
    resource is Channel
) when {
    resource.members.contains(principal) &&
    principal.permits.contains("post")
};

permit (
    principal is Member,
    action == Action::"pin",
    resource is Channel
) when {
    resource.members.contains(principal) &&
    principal.permits.contains("pin") &&
    principal.likedItems.contains("pinning")
};
