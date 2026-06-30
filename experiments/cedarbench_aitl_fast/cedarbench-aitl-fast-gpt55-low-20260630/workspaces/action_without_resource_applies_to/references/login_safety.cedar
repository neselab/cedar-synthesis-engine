// Ceiling: login is permitted for any User on any Session, no conditions.
// Login is the gateway action -- it cannot itself depend on sessionActive
// (which it is what creates).
permit (
    principal is User,
    action == Action::"login",
    resource is Session
);
