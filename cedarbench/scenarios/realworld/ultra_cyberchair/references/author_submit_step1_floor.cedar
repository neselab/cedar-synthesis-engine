permit (principal is User, action == Action::"submitStep1", resource is Submission)
when {
    principal.role == "author"
    && resource.authors.contains(principal)
    && resource.step1Open
};

