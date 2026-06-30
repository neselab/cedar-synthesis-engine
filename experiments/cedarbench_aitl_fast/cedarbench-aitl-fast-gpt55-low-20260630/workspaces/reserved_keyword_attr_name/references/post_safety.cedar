// Ceiling: post only when member AND has "post" capability.
permit (principal is Member, action == Action::"post", resource is Channel)
when {
    resource.members.contains(principal) &&
    principal.permits.contains("post")
};
