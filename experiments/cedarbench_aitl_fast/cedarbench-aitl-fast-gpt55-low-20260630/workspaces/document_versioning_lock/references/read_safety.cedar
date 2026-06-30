// Ceiling: read is permitted for any User on any Document.
// This is maximally permissive — the candidate may be more restrictive
// but must imply this ceiling (any permit must be a subset of this).
permit (
    principal is User,
    action == Action::"read",
    resource is Document
);
