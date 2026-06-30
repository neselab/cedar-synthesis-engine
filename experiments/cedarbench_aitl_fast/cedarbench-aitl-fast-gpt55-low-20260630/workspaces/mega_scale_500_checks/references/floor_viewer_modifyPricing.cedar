// Floor: user with role "viewer" must be permitted to perform action modifyPricing.
permit (
    principal is User,
    action == Action::"modifyPricing",
    resource is Order
)
when {
    principal.role == "viewer"
};
