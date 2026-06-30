permit (
    principal is Approver,
    action == Action::"approve",
    resource is Transaction
)
when {
    principal.role == "teller" &&
    resource.amount.lessThan(decimal("1000.0000")) &&
    context.accumulatedToday.lessThan(resource.dailyLimit)
};

permit (
    principal is Approver,
    action == Action::"approve",
    resource is Transaction
)
when {
    principal.role == "manager" &&
    resource.amount.lessThan(decimal("50000.0000")) &&
    context.accumulatedToday.lessThan(resource.dailyLimit) &&
    (
        !resource.isInternational ||
        resource.amount.lessThan(decimal("10000.0000"))
    )
};

permit (
    principal is Approver,
    action == Action::"approve",
    resource is Transaction
)
when {
    principal.role == "vp"
};

permit (
    principal is Approver,
    action == Action::"reverse",
    resource is Transaction
)
when {
    principal.role == "vp"
};

permit (
    principal is Approver,
    action == Action::"audit",
    resource is Transaction
)
when {
    principal.role == "teller" ||
    principal.role == "manager" ||
    principal.role == "vp"
};