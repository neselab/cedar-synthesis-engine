// Policy store — verified policies appended here

// --- Verified (eval iteration 1) ---
permit (
  principal is User,
  action == Action::"pull",
  resource is Repository
) when {
  principal in resource.readers
};

permit (
  principal is User,
  action == Action::"fork",
  resource is Repository
) when {
  principal in resource.readers
};

permit (
  principal is User,
  action == Action::"push",
  resource is Repository
) when {
  principal in resource.writers
};

permit (
  principal is User,
  action == Action::"assign_issue",
  resource is Issue
) when {
  principal in resource.repo.triagers
};

permit (
  principal is User,
  action == Action::"edit_issue",
  resource is Issue
) when {
  (principal in resource.repo.readers && principal == resource.reporter) ||
  principal in resource.repo.writers
};

permit (
  principal is User,
  action == Action::"delete_issue",
  resource is Issue
) when {
  (principal in resource.repo.readers && principal == resource.reporter) ||
  principal in resource.repo.maintainers
};

permit (
  principal is User,
  action in [
    Action::"add_reader",
    Action::"add_triager",
    Action::"add_writer",
    Action::"add_maintainer",
    Action::"add_admin"
  ],
  resource is Repository
) when {
  principal in resource.admins
};

permit (
  principal is User,
  action == Action::"merge_pr",
  resource is PullRequest
) when {
  principal in resource.repo.writers
};

permit (
  principal is User,
  action == Action::"approve_pr",
  resource is PullRequest
) when {
  principal in resource.repo.readers
};

permit (
  principal is User,
  action == Action::"request_changes",
  resource is PullRequest
) when {
  principal in resource.repo.readers
};

forbid (
  principal is User,
  action in [
    Action::"push",
    Action::"add_reader",
    Action::"add_triager",
    Action::"add_writer",
    Action::"add_maintainer",
    Action::"add_admin"
  ],
  resource is Repository
) when {
  resource.isArchived
};

forbid (
  principal is User,
  action == Action::"merge_pr",
  resource is PullRequest
) when {
  resource.repo.isArchived
};

forbid (
  principal is User,
  action in [
    Action::"approve_pr",
    Action::"request_changes"
  ],
  resource is PullRequest
) when {
  principal == resource.author
};
