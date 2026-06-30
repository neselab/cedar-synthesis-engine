// Floor: `connectInGrace` MUST be permitted in the late portion of the
// grace period — specifically, between 7 and 30 days after expiration.
// A second floor on the grace tier ensures the candidate doesn't cut
// the grace window short (a common bug: encoding a 7-day grace instead
// of 30).
permit (
    principal is Subscriber,
    action == Action::"connectInGrace",
    resource is Service
)
when {
    context.now >= principal.certExpiresAt.offset(duration("7d"))
    && context.now < principal.certExpiresAt.offset(duration("30d"))
};
