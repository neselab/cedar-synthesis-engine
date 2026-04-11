// Floor: a clerk MUST be permitted to initiate a draft payroll entry.
permit (
    principal is User,
    action == Action::"initiate",
    resource is PayrollEntry
)
when {
    principal.role == "clerk"
    && resource.status == "draft"
};
