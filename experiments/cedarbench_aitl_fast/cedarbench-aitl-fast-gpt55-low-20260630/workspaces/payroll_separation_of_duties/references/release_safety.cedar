// Ceiling: release permitted only when principal is a cfo AND entry is
// in approved status.
permit (
    principal is User,
    action == Action::"release",
    resource is PayrollEntry
)
when {
    principal.role == "cfo"
    && resource.status == "approved"
};
