// Floor: user with role "finance_basic" must be permitted to perform action applyDiscount.
permit (
    principal is User,
    action == Action::"applyDiscount",
    resource is Order
)
when {
    principal.role == "finance_basic"
};
