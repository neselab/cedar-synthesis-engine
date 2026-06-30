// Floor: user with role "finance_basic" must be permitted to perform action partialRefund.
permit (
    principal is User,
    action == Action::"partialRefund",
    resource is Order
)
when {
    principal.role == "finance_basic"
};
