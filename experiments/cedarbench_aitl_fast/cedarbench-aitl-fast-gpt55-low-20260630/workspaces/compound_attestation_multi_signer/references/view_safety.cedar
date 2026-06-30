// Ceiling: view is open to any user on any proposal. The ceiling is
// the trivial "always permit" — view has no restrictions in the spec.
permit (
    principal is User,
    action == Action::"view",
    resource is Proposal
);
