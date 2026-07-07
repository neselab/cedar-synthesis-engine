permit (principal is User, action == Action::"submitCameraReady", resource is Submission)
when {
    principal.role == "author"
    && resource.authors.contains(principal)
    && resource.selected
    && resource.reviewProcessDone
};

