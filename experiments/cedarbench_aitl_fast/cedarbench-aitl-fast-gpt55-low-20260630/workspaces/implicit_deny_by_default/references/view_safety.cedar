// Ceiling: view permitted only when principal's role is nurse, doctor,
// or administrator. Any other role string is implicitly denied.
permit (
    principal is Worker,
    action == Action::"view",
    resource is Chart
)
when {
    principal.role == "nurse"
    || principal.role == "doctor"
    || principal.role == "administrator"
};
