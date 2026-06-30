// Floor: an "admin" Employee MUST be able to perform `emergencyAccess`
// from any source IP. Break-glass paths intentionally do NOT exclude
// the compromised range -- the design choice is that an admin can
// always reach the system in an emergency.
permit (
    principal is Employee,
    action == Action::"emergencyAccess",
    resource is InternalSystem
)
when {
    principal.role == "admin"
};
