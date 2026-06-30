// Ceiling: `configure` is permitted only when the principal's role is
// "ops" or "admin", the source IP is inside the admin subnet, and the
// source IP is NOT inside the compromised range.
permit (
    principal is Employee,
    action == Action::"configure",
    resource is InternalSystem
)
when {
    (principal.role == "ops" || principal.role == "admin")
    && context.sourceIp.isInRange(ip("10.20.0.0/24"))
    && !context.sourceIp.isInRange(ip("10.50.0.0/16"))
};
