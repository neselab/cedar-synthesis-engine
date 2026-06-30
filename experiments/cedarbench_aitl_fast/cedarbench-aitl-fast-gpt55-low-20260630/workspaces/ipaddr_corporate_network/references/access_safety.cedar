// Ceiling: `access` is permitted only when the source IP sits in a
// corporate range, NOT in the compromised range, and -- if the resource
// requires VPN -- additionally inside the VPN segment.
permit (
    principal is Employee,
    action == Action::"access",
    resource is InternalSystem
)
when {
    (
        context.sourceIp.isInRange(ip("10.0.0.0/8"))
        || context.sourceIp.isInRange(ip("172.16.0.0/12"))
        || context.sourceIp.isInRange(ip("192.168.0.0/16"))
    )
    && !context.sourceIp.isInRange(ip("10.50.0.0/16"))
    && (
        !resource.requiresVpn
        || context.sourceIp.isInRange(ip("10.10.0.0/16"))
    )
};
