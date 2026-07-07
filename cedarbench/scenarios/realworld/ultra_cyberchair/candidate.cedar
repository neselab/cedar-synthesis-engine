permit (principal, action == Action::"submitStep1", resource)
when {
    principal.role == "author"
    && resource.authors.contains(principal)
    && resource.step1Open
};

permit (principal, action == Action::"submitFullPaper", resource)
when {
    principal.role == "author"
    && resource.authors.contains(principal)
    && resource.step2Open
    && context.hasStep2Credential
};

permit (principal, action == Action::"updateStep1Info", resource)
when {
    principal.role == "author"
    && resource.authors.contains(principal)
    && resource.step2Open
    && context.hasStep2Credential
};

permit (principal, action == Action::"submitCameraReady", resource)
when {
    principal.role == "author"
    && resource.authors.contains(principal)
    && resource.selected
    && resource.reviewProcessDone
};

permit (principal, action in [Action::"downloadPaper", Action::"displayAbstract"], resource)
when {
    principal.role == "reviewer"
    && resource.distributionDone
    && resource.assignedReviewers.contains(principal)
    && !resource.conflictedReviewers.contains(principal)
};

permit (principal, action in [Action::"submitReview", Action::"updateReview"], resource)
when {
    principal.role == "reviewer"
    && resource.reviewOpen
    && resource.assignedReviewers.contains(principal)
    && !resource.conflictedReviewers.contains(principal)
};

permit (principal, action == Action::"readOtherReviews", resource)
when {
    principal.role == "reviewer"
    && resource.assignedReviewers.contains(principal)
    && resource.reviewersSubmitted.contains(principal)
    && !resource.conflictedReviewers.contains(principal)
};

permit (principal, action == Action::"declareConflict", resource)
when {
    principal.role == "reviewer"
    && resource.assignedReviewers.contains(principal)
};

permit (principal, action == Action::"indicateExpertise", resource)
when {
    principal.role == "reviewer"
    && resource.assignedReviewers.contains(principal)
    && (context.expertiseLevel == "X" || context.expertiseLevel == "Y" || context.expertiseLevel == "Z")
};

permit (principal, action == Action::"indicateWillingness", resource)
when {
    principal.role == "reviewer"
    && resource.assignedReviewers.contains(principal)
    && (context.willingness == "R" || context.willingness == "W")
};

permit (principal, action == Action::"volunteerForConflictingPaper", resource)
when {
    principal.role == "reviewer"
    && principal.submittedAllAssignedReviews
    && resource.hasConflictingReviews
    && !resource.conflictedReviewers.contains(principal)
};

permit (principal, action == Action::"monitorReviewProcess", resource)
when {
    (principal.role == "chair" || principal.role == "pcc")
};

permit (principal, action == Action::"askAdditionalReviewer", resource)
when {
    principal.role == "pcc"
    && resource.paper.onlyNonExpertReviews
};

permit (principal, action == Action::"accessReviewerDirectory", resource)
when {
    principal.role == "reviewer"
    && (principal == resource.owner || resource.allowedUsers.contains(principal))
};

permit (principal, action == Action::"readReviewFile", resource)
when {
    principal.role == "reviewer"
    && resource.allowedUsers.contains(principal)
    && (principal == resource.directory.owner || resource.directory.allowedUsers.contains(principal))
};

