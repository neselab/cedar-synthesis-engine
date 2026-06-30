// Floor: user with role "cs_senior" must be permitted to perform action applyDiscount.
permit (
    principal is User,
    action == Action::"applyDiscount",
    resource is Order
)
when {
    principal.role == "cs_senior"
};
