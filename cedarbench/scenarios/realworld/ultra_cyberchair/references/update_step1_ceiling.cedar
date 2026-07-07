permit (principal is User, action == Action::"updateStep1Info", resource is Submission)
when {
    principal.role == "author"
    && resource.authors.contains(principal)
    && resource.step2Open
    && context.hasStep2Credential
};

