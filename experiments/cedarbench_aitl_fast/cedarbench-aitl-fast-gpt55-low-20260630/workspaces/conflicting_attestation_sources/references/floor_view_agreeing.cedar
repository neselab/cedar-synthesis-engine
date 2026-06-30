// Floor: when the principal is the recorded owner AND the request
// asserts a claimedOwner that agrees with the recorded owner, view
// MUST be permitted. (Attesting callers that get it right must not
// be penalised for attesting.)
permit (
    principal is User,
    action == Action::"view",
    resource is Document
)
when {
    principal == resource.recordedOwner
    && context has claimedOwner
    && context.claimedOwner == resource.recordedOwner
};
