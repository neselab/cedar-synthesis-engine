permit (principal is User, action == Action::"updateReview", resource is Submission)
when {
    principal.role == "reviewer"
    && resource.reviewOpen
    && resource.assignedReviewers.contains(principal)
    && !resource.conflictedReviewers.contains(principal)
};

