// Floor: user with role "warehouse" must be permitted to perform action viewPII.
permit (
    principal is User,
    action == Action::"viewPII",
    resource is Order
)
when {
    principal.role == "warehouse"
};
