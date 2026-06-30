// Floor: user with role "returns_lead" must be permitted to perform action bulkOperations.
permit (
    principal is User,
    action == Action::"bulkOperations",
    resource is Order
)
when {
    principal.role == "returns_lead"
};
