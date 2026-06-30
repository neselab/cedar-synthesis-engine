// Ceiling: transfer permitted ONLY when BOTH consents are present, the
// two consent signers cover {owner1, owner2} (in either order), and
// both consents were signed within the last 24h relative to context.now.
//
// Optional record fields require has-guards on every read (§8.3).
// Duration uses Go-style syntax — "24h", not ISO-8601 "PT24H" (§8.9).
permit (
    principal is User,
    action == Action::"transfer",
    resource is JointAsset
)
when {
    context has consent1
    && context has consent2
    && (
        (context.consent1.signer == resource.owner1
         && context.consent2.signer == resource.owner2)
        || (context.consent1.signer == resource.owner2
            && context.consent2.signer == resource.owner1)
    )
    && context.now.durationSince(context.consent1.signedAt) <= duration("24h")
    && context.now.durationSince(context.consent2.signedAt) <= duration("24h")
    && context.now.durationSince(context.consent1.signedAt) >= duration("0h")
    && context.now.durationSince(context.consent2.signedAt) >= duration("0h")
};
