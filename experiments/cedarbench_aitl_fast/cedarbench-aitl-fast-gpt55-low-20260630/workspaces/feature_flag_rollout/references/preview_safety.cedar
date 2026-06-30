// Ceiling: preview permitted only when role is beta_tester or admin.
permit (
    principal is User,
    action == Action::"preview",
    resource is Feature
)
when {
    principal.role == "beta_tester" || principal.role == "admin"
};
