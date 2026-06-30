// Ceiling: approve permitted only when the role/amount/daily-limit/
// international constraints are all satisfied. VPs are exempt from
// the daily-limit and international caps.
permit (
    principal is Approver,
    action == Action::"approve",
    resource is Transaction
)
when {
    principal.role == "vp"
    || (
        principal.role == "teller"
        && resource.amount.lessThan(decimal("1000.0000"))
        && context.accumulatedToday.lessThan(resource.dailyLimit)
        && (!resource.isInternational || resource.amount.lessThan(decimal("10000.0000")))
    )
    || (
        principal.role == "manager"
        && resource.amount.lessThan(decimal("50000.0000"))
        && context.accumulatedToday.lessThan(resource.dailyLimit)
        && (!resource.isInternational || resource.amount.lessThan(decimal("10000.0000")))
    )
};
