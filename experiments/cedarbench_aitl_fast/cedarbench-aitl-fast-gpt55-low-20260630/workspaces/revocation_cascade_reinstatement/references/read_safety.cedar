// Ceiling: read permitted only when EITHER the principal is the owner
// (owner bypass) OR the host has attested that a complete, non-revoked
// grant chain exists (accessAuthorized && !revocationDetected).
//
// Cascade rule: revocationDetected == true overrides accessAuthorized.
// Owners are the root of the chain and are never cascade-invalidated.
permit (
    principal is User,
    action == Action::"read",
    resource is Resource
)
when {
    principal == resource.owner
    || (context.accessAuthorized && !context.revocationDetected)
};
