// Trivial floor: "x" == "x" — tautological.
permit (
    principal is User,
    action == Action::"access",
    resource is Resource
)
when { "x" == "x" };
