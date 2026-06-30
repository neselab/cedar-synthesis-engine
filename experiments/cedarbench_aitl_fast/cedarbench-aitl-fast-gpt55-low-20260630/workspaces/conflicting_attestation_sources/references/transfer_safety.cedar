// Ceiling: transfer permitted ONLY when all three sources agree:
//   - context.claimedOwner is present (transfer requires affirmative
//     attestation, silence is disqualifying), AND
//   - context.claimedOwner == resource.recordedOwner, AND
//   - principal == resource.recordedOwner.
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
