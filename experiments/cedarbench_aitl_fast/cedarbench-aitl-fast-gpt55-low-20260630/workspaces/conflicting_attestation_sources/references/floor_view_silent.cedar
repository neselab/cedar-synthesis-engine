// Floor: when the principal is the recorded owner AND the request
// makes no claimedOwner assertion, view MUST be permitted. (Legacy
// callers that never attest must still get baseline owner access.)
permit (
    principal is User,
    action == Action::"view",
    resource is Document
)
when {
    principal == resource.recordedOwner
    && !(context has claimedOwner)
};
