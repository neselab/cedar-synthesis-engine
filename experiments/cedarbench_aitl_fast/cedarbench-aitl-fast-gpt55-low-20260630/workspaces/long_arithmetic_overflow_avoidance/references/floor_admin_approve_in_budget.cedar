// Floor: an admin approver with a positive in-budget request MUST be permitted to approveSpend.
permit (
    principal is Approver,
    action == Action::"approveSpend",
    resource is Project
)
when {
    principal.role == "admin"
    && context.requestedAmount > 0
    && resource.spentSoFar < resource.monthlyBudget
    && context.requestedAmount <= resource.monthlyBudget - resource.spentSoFar
};
