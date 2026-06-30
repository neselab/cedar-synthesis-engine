// Floor: the owner MUST be able to read their own document.
// Same rule as the ceiling — there is only one rule in this spec.
permit (
    principal is User,
    action == Action::"read",
    resource is Document
)
when {
    principal == resource.owner
};
