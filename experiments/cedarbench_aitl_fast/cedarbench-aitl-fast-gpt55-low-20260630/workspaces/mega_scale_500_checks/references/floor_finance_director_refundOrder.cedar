// Floor: user with role "finance_director" must be permitted to perform action refundOrder.
permit (
    principal is User,
    action == Action::"refundOrder",
    resource is Order
)
when {
    principal.role == "finance_director"
};
