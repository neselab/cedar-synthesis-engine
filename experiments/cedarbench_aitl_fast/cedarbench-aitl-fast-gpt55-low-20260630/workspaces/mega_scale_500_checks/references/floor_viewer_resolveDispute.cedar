// Floor: user with role "viewer" must be permitted to perform action resolveDispute.
permit (
    principal is User,
    action == Action::"resolveDispute",
    resource is Order
)
when {
    principal.role == "viewer"
};
