forbid (
    principal is User,
    action == Action::"push",
    resource is Repository
)
when {
    resource.isArchived == true
};

forbid (
    principal is User,
    action in [
        Action::"add_reader",
        Action::"add_triager",
        Action::"add_writer",
        Action::"add_maintainer",
        Action::"add_admin"
    ],
    resource is Repository
)
when {
    resource.isArchived == true
};

forbid (
    principal is User,
    action == Action::"merge_pr",
    resource is PullRequest
)
when {
    resource.repo.isArchived == true
};

forbid (
    principal is User,
    action == Action::"fork",
    resource is Repository
)
when {
    resource.isPrivate == true
};

forbid (
    principal is User,
    action == Action::"edit_issue",
    resource is Issue
)
when {
    resource.isLocked == true
};

forbid (
    principal is User,
    action == Action::"approve_pr",
    resource is PullRequest
)
when {
    principal == resource.author
};

permit (
    principal is User,
    action == Action::"pull",
    resource is Repository
)
when {
    principal in resource.readers
};

permit (
    principal is User,
    action == Action::"fork",
    resource is Repository
)
when {
    principal in resource.readers
};

permit (
    principal is User,
    action == Action::"push",
    resource is Repository
)
when {
    principal in resource.contributors ||
    principal in resource.writers ||
    principal in resource.maintainers ||
    principal in resource.admins
};

permit (
    principal is User,
    action == Action::"delete_issue",
    resource is Issue
)
when {
    principal in resource.repo.readers &&
    principal == resource.reporter
};

permit (
    principal is User,
    action == Action::"edit_issue",
    resource is Issue
)
when {
    principal in resource.repo.readers &&
    principal == resource.reporter
};

permit (
    principal is User,
    action == Action::"close_issue",
    resource is Issue
)
when {
    principal in resource.repo.readers &&
    principal == resource.reporter
};

permit (
    principal is User,
    action == Action::"assign_issue",
    resource is Issue
)
when {
    principal in resource.repo.triagers ||
    principal in resource.repo.writers ||
    principal in resource.repo.maintainers ||
    principal in resource.repo.admins
};

permit (
    principal is User,
    action == Action::"edit_issue",
    resource is Issue
)
when {
    principal in resource.repo.writers ||
    principal in resource.repo.admins
};

permit (
    principal is User,
    action == Action::"close_issue",
    resource is Issue
)
when {
    principal in resource.repo.writers ||
    principal in resource.repo.admins
};

permit (
    principal is User,
    action == Action::"delete_issue",
    resource is Issue
)
when {
    principal in resource.repo.maintainers ||
    principal in resource.repo.admins
};

permit (
    principal is User,
    action == Action::"merge_pr",
    resource is PullRequest
)
when {
    principal in resource.repo.writers ||
    principal in resource.repo.maintainers ||
    principal in resource.repo.admins
};

permit (
    principal is User,
    action == Action::"approve_pr",
    resource is PullRequest
)
when {
    principal in resource.repo.readers ||
    principal in resource.repo.triagers ||
    principal in resource.repo.contributors ||
    principal in resource.repo.writers ||
    principal in resource.repo.maintainers ||
    principal in resource.repo.admins
};

permit (
    principal is User,
    action == Action::"add_reader",
    resource is Repository
)
when {
    principal in resource.admins
};

permit (
    principal is User,
    action == Action::"add_triager",
    resource is Repository
)
when {
    principal in resource.admins
};

permit (
    principal is User,
    action == Action::"add_writer",
    resource is Repository
)
when {
    principal in resource.admins
};

permit (
    principal is User,
    action == Action::"add_maintainer",
    resource is Repository
)
when {
    principal in resource.admins
};

permit (
    principal is User,
    action == Action::"add_admin",
    resource is Repository
)
when {
    principal in resource.admins
};