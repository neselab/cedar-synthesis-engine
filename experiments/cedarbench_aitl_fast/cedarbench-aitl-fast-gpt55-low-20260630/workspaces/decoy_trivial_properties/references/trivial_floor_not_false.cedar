// Trivial floor: !(1 == 2) — tautological.
permit (
    principal is User,
    action == Action::"access",
    resource is Resource
)
when { !(1 == 2) };
