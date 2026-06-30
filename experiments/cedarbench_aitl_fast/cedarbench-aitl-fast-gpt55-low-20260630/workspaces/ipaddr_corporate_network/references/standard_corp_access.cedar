// Floor: a "standard" Employee from a corporate range MUST be able to
// `access` an InternalSystem that does NOT require VPN, provided the
// source IP is not in the compromised range.
//
// The floor repeats the global compromised-range exclusion (§8.8 floor
// consistency) so it is jointly satisfiable with every ceiling.
permit (
    principal is Employee,
    action == Action::"access",
    resource is InternalSystem
)
when {
    principal.role == "standard"
    && resource.requiresVpn == false
    && (
        context.sourceIp.isInRange(ip("10.0.0.0/8"))
        || context.sourceIp.isInRange(ip("172.16.0.0/12"))
        || context.sourceIp.isInRange(ip("192.168.0.0/16"))
    )
    && !context.sourceIp.isInRange(ip("10.50.0.0/16"))
};
