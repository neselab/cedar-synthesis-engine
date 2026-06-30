// Policy store — verified policies appended here

// --- Verified (eval iteration 1) ---
permit (
    principal is User,
    action == Action::"view",
    resource is Document
)
when {
    principal == resource.recordedOwner
    && (
        !(context has claimedOwner)
        || (context has claimedOwner && context.claimedOwner == resource.recordedOwner)
    )
};

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
