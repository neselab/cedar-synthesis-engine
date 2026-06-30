// Floor: a `transfer` Transaction whose amount equals exactly the
// upper bound (decimal("1000000.0000")) MUST be permitted. The
// `lessThanOrEqual` in the ceiling is inclusive, and this floor
// pins that inclusivity so the candidate cannot accidentally use
// `lessThan` and exclude the boundary.
permit (
    principal is User,
    action == Action::"transfer",
    resource is Transaction
)
when {
    resource.amount.greaterThanOrEqual(decimal("1000000.0000"))
    && resource.amount.lessThanOrEqual(decimal("1000000.0000"))
};
