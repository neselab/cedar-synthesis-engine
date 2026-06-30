// Floor: user with role "viewer" must be permitted to perform action applyDiscount.
permit (
    principal is User,
    action == Action::"applyDiscount",
    resource is Order
)
when {
    principal.role == "viewer"
};
