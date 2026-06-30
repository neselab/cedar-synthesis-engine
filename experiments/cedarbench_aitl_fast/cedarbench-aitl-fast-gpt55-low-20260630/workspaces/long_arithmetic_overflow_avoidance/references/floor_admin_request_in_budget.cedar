// Floor: an admin approver with a positive in-budget request MUST be permitted to requestSpend.
permit (
    principal is Approver,
    action == Action::"requestSpend",
    resource is Project
)
when {
    principal.role == "admin"
    && context.requestedAmount > 0
    && resource.spentSoFar < resource.monthlyBudget
    && context.requestedAmount <= resource.monthlyBudget - resource.spentSoFar
};
