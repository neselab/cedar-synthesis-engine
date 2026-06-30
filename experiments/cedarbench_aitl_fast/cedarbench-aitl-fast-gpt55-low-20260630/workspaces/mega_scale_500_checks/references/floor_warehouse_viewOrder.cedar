// Floor: user with role "warehouse" must be permitted to perform action viewOrder.
permit (
    principal is User,
    action == Action::"viewOrder",
    resource is Order
)
when {
    principal.role == "warehouse"
};
