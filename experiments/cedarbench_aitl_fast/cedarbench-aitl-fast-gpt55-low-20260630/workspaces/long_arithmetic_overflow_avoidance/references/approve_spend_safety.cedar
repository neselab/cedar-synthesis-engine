// Ceiling: approveSpend requires admin role AND safe budget check.
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
