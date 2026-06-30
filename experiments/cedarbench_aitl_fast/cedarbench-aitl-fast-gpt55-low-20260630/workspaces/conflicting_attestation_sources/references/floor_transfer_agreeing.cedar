// Floor: when all three sources agree (claimedOwner present,
// claimedOwner == recordedOwner, principal == recordedOwner),
// transfer MUST be permitted.
permit (
    principal is User,
    action == Action::"transfer",
    resource is Document
)
when {
    context has claimedOwner
    && context.claimedOwner == resource.recordedOwner
    && principal == resource.recordedOwner
};
