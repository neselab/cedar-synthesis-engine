// Floor: user with role "cs_agent" must be permitted to perform action modifyPricing.
permit (
    principal is User,
    action == Action::"modifyPricing",
    resource is Order
)
when {
    principal.role == "cs_agent"
};
