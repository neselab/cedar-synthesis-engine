// Ceiling: initiate permitted only when principal is a clerk AND
// entry is in draft status.
permit (
    principal is User,
    action == Action::"initiate",
    resource is PayrollEntry
)
when {
    principal.role == "clerk"
    && resource.status == "draft"
};
