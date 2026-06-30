// Ceiling: read permitted unconditionally (transparency requirement).
permit (
    principal is User,
    action == Action::"read",
    resource is PayrollEntry
);
