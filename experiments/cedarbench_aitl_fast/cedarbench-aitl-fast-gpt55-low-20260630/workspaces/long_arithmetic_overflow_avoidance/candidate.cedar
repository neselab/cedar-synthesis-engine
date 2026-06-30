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