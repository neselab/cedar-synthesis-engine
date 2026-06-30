// Floor: an "ops" Employee whose request originates from the admin
// subnet (10.20.0.0/24) MUST be able to `configure` an InternalSystem.
//
// The admin subnet does not overlap the compromised range; the
// exclusion is repeated for §8.8 floor consistency with the ceiling.
permit (
    principal is Employee,
    action == Action::"configure",
    resource is InternalSystem
)
when {
    principal.role == "ops"
    && context.sourceIp.isInRange(ip("10.20.0.0/24"))
    && !context.sourceIp.isInRange(ip("10.50.0.0/16"))
};
