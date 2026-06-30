// Floor: a member approver with a positive in-budget request MUST be permitted to requestSpend.
// Encoded with the SAFE arithmetic form to avoid overflow.
permit (
    principal is Approver,
    action == Action::"requestSpend",
    resource is Project
)
when {
    principal.role == "member"
    && context.requestedAmount > 0
    && resource.spentSoFar < resource.monthlyBudget
    && context.requestedAmount <= resource.monthlyBudget - resource.spentSoFar
};
