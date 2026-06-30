// Floor: a non-owner principal whose grant chain has been attested as
// fully active (accessAuthorized) and not cascade-revoked
// (!revocationDetected) MUST be permitted to read.
permit (
    principal is User,
    action == Action::"read",
    resource is Resource
)
when {
    principal != resource.owner
    && context.accessAuthorized
    && !context.revocationDetected
};
