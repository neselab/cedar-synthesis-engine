// Floor: any User MUST be permitted to log in (no preconditions).
// Login is the universal entry point.
permit (
    principal is User,
    action == Action::"login",
    resource is Session
);
