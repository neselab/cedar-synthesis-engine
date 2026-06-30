// Floor: the owner MUST retain read-only access to their own document
// even after it is archived (records retention exception). This is the
// narrow exception that defeats the naive permit-overrides-forbid pattern.
permit (
    principal is User,
    action == Action::"view",
    resource is Document
)
when {
    principal == resource.owner && resource.archived
};
