// Floor: the owner MUST be permitted to view their document UNLESS
// it is quarantined. The `!resource.quarantined` clause is the §8.8
// floor-bound consistency exclusion for the global quarantine
// forbid. Without this carve-out, this floor would be jointly
// unsatisfiable with the view_safety ceiling on quarantined
// documents owned by the principal.
permit (
    principal is User,
    action == Action::"view",
    resource is Document
)
when {
    principal == resource.owner
    && !resource.quarantined
};
