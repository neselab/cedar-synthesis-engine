// Floor: any User attempting a `transfer` Transaction whose amount is
// strictly positive AND at most one million MUST be permitted. Pins
// the candidate's bounds to be no tighter than the spec on either side.
permit (
    principal is User,
    action == Action::"transfer",
    resource is Transaction
)
when {
    resource.amount.greaterThan(decimal("0.0000"))
    && resource.amount.lessThanOrEqual(decimal("1000000.0000"))
};
