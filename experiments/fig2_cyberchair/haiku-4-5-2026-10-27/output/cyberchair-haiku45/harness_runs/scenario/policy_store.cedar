// Policy store — verified policies appended here

// --- Verified (eval iteration 2) ---
permit (principal, action == Action::"submitStep1", resource)
when {
    principal in resource.authors && resource.step1Open
};

permit (principal, action == Action::"submitFullPaper", resource)
when {
    principal in resource.authors && context.hasStep2Credential && resource.step2Open
};

permit (principal, action == Action::"updateStep1Info", resource)
when {
    principal in resource.authors && resource.step2Open
};

permit (principal, action == Action::"submitCameraReady", resource)
when {
    principal in resource.authors && resource.selected && resource.reviewProcessDone
};

permit (principal, action == Action::"downloadPaper", resource)
when {
    principal in resource.assignedReviewers && resource.distributionDone && !(principal in resource.conflictedReviewers)
};

permit (principal, action == Action::"submitReview", resource)
when {
    principal in resource.assignedReviewers && !(principal in resource.conflictedReviewers) && resource.reviewOpen
};

permit (principal, action == Action::"updateReview", resource)
when {
    principal in resource.assignedReviewers && !(principal in resource.conflictedReviewers) && resource.reviewOpen
};

permit (principal, action == Action::"readOtherReviews", resource)
when {
    principal in resource.reviewersSubmitted
};

permit (principal, action == Action::"declareConflict", resource)
when {
    principal in resource.assignedReviewers
};

permit (principal, action == Action::"volunteerForConflictingPaper", resource)
when {
    principal.role == "Reviewer" && principal.submittedAllAssignedReviews && !(principal in resource.conflictedReviewers)
};

permit (principal, action == Action::"monitorReviewProcess", resource)
when {
    principal.role == "Chair" || principal.role == "PCC"
};

permit (principal, action == Action::"askAdditionalReviewer", resource)
when {
    principal.role == "PCC" && resource.paper.onlyNonExpertReviews
};

permit (principal, action == Action::"accessReviewerDirectory", resource)
when {
    principal in resource.allowedUsers
};

permit (principal, action == Action::"readReviewFile", resource)
when {
    principal in resource.directory.allowedUsers
};
