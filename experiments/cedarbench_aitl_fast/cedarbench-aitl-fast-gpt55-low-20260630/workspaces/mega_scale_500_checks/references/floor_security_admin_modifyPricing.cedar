// Floor: user with role "security_admin" must be permitted to perform action modifyPricing.
permit (
    principal is User,
    action == Action::"modifyPricing",
    resource is Order
)
when {
    principal.role == "security_admin"
};
