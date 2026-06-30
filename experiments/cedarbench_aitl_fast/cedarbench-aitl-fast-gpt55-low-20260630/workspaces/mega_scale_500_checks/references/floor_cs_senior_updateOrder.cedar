// Floor: user with role "cs_senior" must be permitted to perform action updateOrder.
permit (
    principal is User,
    action == Action::"updateOrder",
    resource is Order
)
when {
    principal.role == "cs_senior"
};
