// Floor: user with role "finance_director" must be permitted to perform action createOrder.
permit (
    principal is User,
    action == Action::"createOrder",
    resource is Order
)
when {
    principal.role == "finance_director"
};
