// Floor: a manager MUST be permitted to approve a mid-sized domestic
// transaction when they are still under their daily limit.
permit (
    principal is Approver,
    action == Action::"approve",
    resource is Transaction
)
when {
    principal.role == "manager"
    && resource.amount.lessThan(decimal("50000.0000"))
    && !resource.isInternational
    && context.accumulatedToday.lessThan(resource.dailyLimit)
};
