// Floor: user with role "finance_manager" must be permitted to perform action resolveDispute.
permit (
    principal is User,
    action == Action::"resolveDispute",
    resource is Order
)
when {
    principal.role == "finance_manager"
};
