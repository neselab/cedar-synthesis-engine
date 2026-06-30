// Ceiling: withdraw permitted only when the account balance is strictly
// positive. "Strictly positive" expressed as the threshold comparison
// `balance > 0.0001`, since Cedar decimal has 4-digit fractional
// precision and 0.0001 is the smallest representable positive value.
permit (
    principal is User,
    action == Action::"withdraw",
    resource is Account
)
when {
    resource.balance.greaterThan(decimal("0.0001"))
};
