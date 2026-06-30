// Ceiling: requestSpend permitted only with safe budget check.
// SAFE form: requestedAmount <= monthlyBudget - spentSoFar
// (avoids spentSoFar + requestedAmount overflow at runtime).
permit (
    principal is Approver,
    action == Action::"requestSpend",
    resource is Project
)
when {
    context.requestedAmount > 0
    && resource.spentSoFar < resource.monthlyBudget
    && context.requestedAmount <= resource.monthlyBudget - resource.spentSoFar
};
