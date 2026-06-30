// Ceiling: edit permitted only when principal's role is doctor or
// administrator. Nurses and any other role are implicitly denied.
permit (
    principal is Worker,
    action == Action::"edit",
    resource is Chart
)
when {
    principal.role == "doctor"
    || principal.role == "administrator"
};
