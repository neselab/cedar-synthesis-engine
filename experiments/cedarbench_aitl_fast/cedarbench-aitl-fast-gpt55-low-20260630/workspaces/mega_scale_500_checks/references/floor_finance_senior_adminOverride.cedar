// Floor: user with role "finance_senior" must be permitted to perform action adminOverride.
permit (
    principal is User,
    action == Action::"adminOverride",
    resource is Order
)
when {
    principal.role == "finance_senior"
};
