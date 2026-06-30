// Floor: user with role "returns_lead" must be permitted to perform action shipOrder.
permit (
    principal is User,
    action == Action::"shipOrder",
    resource is Order
)
when {
    principal.role == "returns_lead"
};
