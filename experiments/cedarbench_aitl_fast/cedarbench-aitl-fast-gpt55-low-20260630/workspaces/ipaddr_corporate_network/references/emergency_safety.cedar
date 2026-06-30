// Ceiling: `emergencyAccess` is permitted only when the principal's
// role is "admin". The break-glass path intentionally places no IP
// restriction, so the only safety bound is the role gate.
permit (
    principal is Employee,
    action == Action::"emergencyAccess",
    resource is InternalSystem
)
when {
    principal.role == "admin"
};
