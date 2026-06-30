// Floor: any user MUST be permitted to read any payroll entry
// (transparency requirement).
permit (
    principal is User,
    action == Action::"read",
    resource is PayrollEntry
);
