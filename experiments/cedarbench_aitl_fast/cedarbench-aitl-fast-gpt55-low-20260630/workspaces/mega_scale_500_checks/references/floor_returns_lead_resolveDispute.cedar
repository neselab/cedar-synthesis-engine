// Floor: user with role "returns_lead" must be permitted to perform action resolveDispute.
permit (
    principal is User,
    action == Action::"resolveDispute",
    resource is Order
)
when {
    principal.role == "returns_lead"
};
