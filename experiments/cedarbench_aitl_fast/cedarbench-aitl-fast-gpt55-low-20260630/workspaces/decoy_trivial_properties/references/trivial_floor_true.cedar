// Trivial floor: vacuously satisfied.
permit (
    principal is User,
    action == Action::"access",
    resource is Resource
)
when { true };
