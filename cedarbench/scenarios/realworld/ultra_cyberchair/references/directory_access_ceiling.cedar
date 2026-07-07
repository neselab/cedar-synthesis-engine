permit (principal is User, action == Action::"accessReviewerDirectory", resource is ReviewerDirectory)
when {
    principal.role == "reviewer"
    && (principal == resource.owner || resource.allowedUsers.contains(principal))
};

