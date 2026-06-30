// Ceiling: transfer permitted only when the transaction amount is
// strictly positive AND at most one million. Both bounds expressed via
// decimal method-style comparisons because Cedar does not overload
// `<`, `>`, `<=`, `>=` for decimal.
permit (
    principal is User,
    action == Action::"transfer",
    resource is Transaction
)
when {
    resource.amount.greaterThan(decimal("0.0000"))
    && resource.amount.lessThanOrEqual(decimal("1000000.0000"))
};
