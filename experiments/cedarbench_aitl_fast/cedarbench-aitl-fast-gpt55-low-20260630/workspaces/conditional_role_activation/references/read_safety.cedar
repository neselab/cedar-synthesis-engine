// Ceiling: read on a SecureSystem is permitted for any Employee. There
// are no network or role restrictions on read.
permit (
    principal is Employee,
    action == Action::"read",
    resource is SecureSystem
);
