// Floor: user with role "warehouse" must be permitted to perform action maskPII.
permit (
    principal is User,
    action == Action::"maskPII",
    resource is Order
)
when {
    principal.role == "warehouse"
};
