// Floor: `connect` MUST be permitted when the current time is strictly
// more than 7 days before expiration (tier 1 — pre-warning). Encodes the
// liveness of normal connections during the bulk of the certificate's
// lifetime.
permit (
    principal is Subscriber,
    action == Action::"connect",
    resource is Service
)
when {
    context.now < principal.certExpiresAt.offset(duration("-7d"))
};
