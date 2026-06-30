permit (
    principal,
    action == Action::"pull",
    resource
)
when {
    principal is User &&
    resource is Repository &&
    principal in resource.readers
};

permit (
    principal,
    action == Action::"fork",
    resource
)
when {
    principal is User &&
    resource is Repository &&
    principal in resource.readers
};

permit (
    principal,
    action == Action::"push",
    resource
)
when {
    principal is User &&
    resource is Repository &&
    principal in resource.writers
};

permit (
    principal,
    action == Action::"assign_issue",
    resource
)
when {
    principal is User &&
    resource is Issue &&
    principal in resource.repo.triagers
};

permit (
    principal,
    action == Action::"edit_issue",
    resource
)
when {
    principal is User &&
    resource is Issue &&
    principal in resource.repo.readers &&
    principal == resource.reporter
};

permit (
    principal,
    action == Action::"edit_issue",
    resource
)
when {
    principal is User &&
    resource is Issue &&
    principal in resource.repo.writers
};

permit (
    principal,
    action == Action::"delete_issue",
    resource
)
when {
    principal is User &&
    resource is Issue &&
    principal in resource.repo.readers &&
    principal == resource.reporter
};

permit (
    principal,
    action == Action::"delete_issue",
    resource
)
when {
    principal is User &&
    resource is Issue &&
    principal in resource.repo.maintainers
};

permit (
    principal,
    action in [
        Action::"add_reader",
        Action::"add_triager",
        Action::"add_writer",
        Action::"add_maintainer",
        Action::"add_admin"
    ],
    resource
)
when {
    principal is User &&
    resource is Repository &&
    principal in resource.admins
};

forbid (
    principal,
    action in [
        Action::"push",
        Action::"add_reader",
        Action::"add_triager",
        Action::"add_writer",
        Action::"add_maintainer",
        Action::"add_admin"
    ],
    resource
)
when {
    principal is User &&
    resource is Repository &&
    resource.isArchived == true
};

forbid (
    principal,
    action in [
        Action::"add_reader",
        Action::"add_triager",
        Action::"add_writer",
        Action::"add_maintainer",
        Action::"add_admin"
    ],
    resource
)
when {
    principal is User &&
    resource is Repository &&
    resource.collaboratorCount >= resource.maxCollaborators
};

forbid (
    principal,
    action == Action::"push",
    resource
)
when {
    principal is User &&
    resource is Repository &&
    principal.accountAgeDays < 30
};