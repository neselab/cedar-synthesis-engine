// Floor: a CFO MUST be permitted to release an approved payroll entry.
permit (
    principal is User,
    action == Action::"release",
    resource is PayrollEntry
)
when {
    principal.role == "cfo"
    && resource.status == "approved"
};
