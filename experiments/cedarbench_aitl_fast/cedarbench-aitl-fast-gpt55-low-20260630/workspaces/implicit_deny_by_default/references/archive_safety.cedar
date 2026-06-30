// Ceiling: archive permitted only when principal's role is administrator.
// Nurses, doctors, and any other role are implicitly denied.
permit (
    principal is Worker,
    action == Action::"archive",
    resource is Chart
)
when {
    principal.role == "administrator"
};
