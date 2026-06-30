// Ceiling: view permitted ONLY when the principal is an active
// employee. Inactive employees (terminated, on_leave, suspended,
// any non-"active" status) MUST be denied view.
permit (
    principal is Employee,
    action == Action::"view",
    resource is Resource
)
when {
    principal.employmentStatus == "active"
};
