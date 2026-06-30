// Floor: user with role "finance_senior" must be permitted to perform action markDelivered.
permit (
    principal is User,
    action == Action::"markDelivered",
    resource is Order
)
when {
    principal.role == "finance_senior"
};
