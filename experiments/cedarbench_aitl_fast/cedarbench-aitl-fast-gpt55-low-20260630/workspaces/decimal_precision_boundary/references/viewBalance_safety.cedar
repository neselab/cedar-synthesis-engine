// Ceiling: viewBalance is unrestricted -- any User may view any
// Account's balance. The ceiling is `permit` with no additional
// `when` clause, so any candidate that adds restrictions is still
// implied by this reference (more restrictive => still implied).
permit (
    principal is User,
    action == Action::"viewBalance",
    resource is Account
);
