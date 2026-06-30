// Policy store — verified policies appended here

// --- Verified (eval iteration 1) ---
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
  principal in resource.writers
};

permit (
  principal is User,
  action == Action::"assign_issue",
  resource is Issue
)
when {
  principal in resource.repo.triagers
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
  action == Action::"edit_issue",
  resource is Issue
)
when {
  principal in resource.repo.writers
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
  action == Action::"delete_issue",
  resource is Issue
)
when {
  principal in resource.repo.maintainers
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
)
when {
  resource.isArchived
};

forbid (
  principal is User,
  action == Action::"edit_issue",
  resource is Issue
)
when {
  resource.isLocked
};
