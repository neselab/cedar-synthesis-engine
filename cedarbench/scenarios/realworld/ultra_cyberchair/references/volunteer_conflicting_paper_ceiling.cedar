permit (principal is User, action == Action::"volunteerForConflictingPaper", resource is Submission)
when {
    principal.role == "reviewer"
    && principal.submittedAllAssignedReviews
    && resource.hasConflictingReviews
    && !resource.conflictedReviewers.contains(principal)
};

