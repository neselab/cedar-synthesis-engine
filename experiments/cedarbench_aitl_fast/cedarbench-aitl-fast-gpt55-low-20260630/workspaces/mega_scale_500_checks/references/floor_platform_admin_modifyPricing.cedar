// Floor: user with role "platform_admin" must be permitted to perform action modifyPricing.
permit (
    principal is User,
    action == Action::"modifyPricing",
    resource is Order
)
when {
    principal.role == "platform_admin"
};
