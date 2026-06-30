// Floor: a teller MUST be permitted to approve a small domestic
// transaction when they are still under their daily limit.
permit (
    principal is Approver,
    action == Action::"approve",
    resource is Transaction
)
when {
    principal.role == "teller"
    && resource.amount.lessThan(decimal("1000.0000"))
    && !resource.isInternational
    && context.accumulatedToday.lessThan(resource.dailyLimit)
};
