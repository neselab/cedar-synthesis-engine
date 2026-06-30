// Floor: any Employee MUST be permitted to read a SecureSystem.
permit (
    principal is Employee,
    action == Action::"read",
    resource is SecureSystem
);
