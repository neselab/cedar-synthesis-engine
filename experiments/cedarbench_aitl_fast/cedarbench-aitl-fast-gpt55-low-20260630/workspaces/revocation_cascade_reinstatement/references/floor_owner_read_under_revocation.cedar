// Floor: an owner MUST be able to read their own resource even when
// the host reports revocationDetected == true. Owners are the root of
// the grant chain; cascade revocation never invalidates the owner's
// own access. Catches the bug where the owner branch is incorrectly
// gated on !context.revocationDetected.
permit (
    principal is User,
    action == Action::"read",
    resource is Resource
)
when {
    principal == resource.owner
    && context.revocationDetected
};
