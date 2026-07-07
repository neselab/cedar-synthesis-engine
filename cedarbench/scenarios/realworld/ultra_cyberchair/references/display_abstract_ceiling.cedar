permit (principal is User, action == Action::"displayAbstract", resource is Submission)
when {
    principal.role == "reviewer"
    && resource.distributionDone
    && resource.assignedReviewers.contains(principal)
    && !resource.conflictedReviewers.contains(principal)
};

