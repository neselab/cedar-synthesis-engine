// Floor: user with role "finance_senior" must be permitted to perform action cancelOrder.
permit (
    principal is User,
    action == Action::"cancelOrder",
    resource is Order
)
when {
    principal.role == "finance_senior"
};
