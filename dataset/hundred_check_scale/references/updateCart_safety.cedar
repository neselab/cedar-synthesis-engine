// Ceiling: updateCart permitted only for the listed roles and statuses.
permit (
    principal is User,
    action == Action::"updateCart",
    resource is Order
)
when {
    (principal.role == "viewer" || principal.role == "cs_agent" || principal.role == "cs_manager")
    && (resource.status == "cart")
};
