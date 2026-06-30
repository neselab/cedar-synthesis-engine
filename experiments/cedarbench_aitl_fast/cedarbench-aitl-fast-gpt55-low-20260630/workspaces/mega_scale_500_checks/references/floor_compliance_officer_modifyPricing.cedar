// Floor: user with role "compliance_officer" must be permitted to perform action modifyPricing.
permit (
    principal is User,
    action == Action::"modifyPricing",
    resource is Order
)
when {
    principal.role == "compliance_officer"
};
