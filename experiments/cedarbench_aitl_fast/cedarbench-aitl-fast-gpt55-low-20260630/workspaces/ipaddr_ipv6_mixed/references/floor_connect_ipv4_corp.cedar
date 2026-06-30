// Floor: an Operator with an IPv4 corporate-range client IP MUST be
// permitted to connect to an IPv4 server (same-family case).
permit (
    principal is Operator,
    action == Action::"connect",
    resource is Server
)
when {
    context.clientIp.isIpv4()
    && context.clientIp.isInRange(ip("10.0.0.0/8"))
    && resource.serverIp.isIpv4()
};
