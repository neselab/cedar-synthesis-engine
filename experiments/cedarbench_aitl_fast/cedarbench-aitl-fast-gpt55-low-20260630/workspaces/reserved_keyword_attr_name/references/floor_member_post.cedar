// Floor: a member with "post" capability MUST be permitted to post.
permit (principal is Member, action == Action::"post", resource is Channel)
when {
    resource.members.contains(principal) &&
    principal.permits.contains("post")
};
