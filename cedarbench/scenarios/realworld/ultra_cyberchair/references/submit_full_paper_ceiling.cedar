permit (principal is User, action == Action::"submitFullPaper", resource is Submission)
when {
    principal.role == "author"
    && resource.authors.contains(principal)
    && resource.step2Open
    && context.hasStep2Credential
};

