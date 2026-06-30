// Floor: an Operator with an IPv6 corporate-range client IP MUST be
// permitted to connect to an IPv6 server (same-family case).
permit (
    principal is Operator,
    action == Action::"connect",
    resource is Server
)
when {
    context.clientIp.isIpv6()
    && context.clientIp.isInRange(ip("2001:db8::/48"))
    && resource.serverIp.isIpv6()
};
