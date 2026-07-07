permit (principal is User, action == Action::"readOtherReviews", resource is Submission)
when {
    principal.role == "reviewer"
    && resource.assignedReviewers.contains(principal)
    && resource.reviewersSubmitted.contains(principal)
    && !resource.conflictedReviewers.contains(principal)
};

