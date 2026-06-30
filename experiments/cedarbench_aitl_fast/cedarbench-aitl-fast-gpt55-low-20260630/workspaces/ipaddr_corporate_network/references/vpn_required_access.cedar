// Floor: an Employee on the VPN segment (10.10.0.0/16) MUST be able
// to `access` a VPN-required InternalSystem.
//
// The VPN segment is inside 10.0.0.0/8, so the corporate-range
// requirement is satisfied transitively. The floor repeats the
// compromised-range exclusion to remain jointly satisfiable with the
// ceiling (§8.8).
permit (
    principal is Employee,
    action == Action::"access",
    resource is InternalSystem
)
when {
    resource.requiresVpn == true
    && context.sourceIp.isInRange(ip("10.10.0.0/16"))
    && !context.sourceIp.isInRange(ip("10.50.0.0/16"))
};
