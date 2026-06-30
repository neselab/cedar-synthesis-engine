// Floor: when both consents are present, signed by the two owners (in
// canonical order — consent1 = owner1, consent2 = owner2), and both
// were signed within the last 24h, transfer MUST be permitted.
//
// This floor encodes the canonical signer order. The "either order"
// flexibility is enforced by the ceiling, not the floor — the floor
// just needs to pin down ONE concrete permitted scenario.
//
// Every optional field read sits behind a `context has consentN`
// guard (§8.3). All global-forbid checks are vacuous here (no global
// forbids in this scenario).
permit (
    principal is User,
    action == Action::"transfer",
    resource is JointAsset
)
when {
    context has consent1
    && context has consent2
    && context.consent1.signer == resource.owner1
    && context.consent2.signer == resource.owner2
    && context.now.durationSince(context.consent1.signedAt) <= duration("24h")
    && context.now.durationSince(context.consent2.signedAt) <= duration("24h")
    && context.now.durationSince(context.consent1.signedAt) >= duration("0h")
    && context.now.durationSince(context.consent2.signedAt) >= duration("0h")
};
