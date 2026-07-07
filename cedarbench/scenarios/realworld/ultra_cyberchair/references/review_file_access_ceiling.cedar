permit (principal is User, action == Action::"readReviewFile", resource is ReviewFile)
when {
    principal.role == "reviewer"
    && resource.allowedUsers.contains(principal)
    && (principal == resource.directory.owner || resource.directory.allowedUsers.contains(principal))
};

