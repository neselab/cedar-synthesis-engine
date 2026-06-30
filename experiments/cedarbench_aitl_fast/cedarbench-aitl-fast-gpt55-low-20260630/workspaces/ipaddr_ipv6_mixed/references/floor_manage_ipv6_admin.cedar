// Floor: an Operator on the IPv6 admin subnet (2001:db8:1::/64) MUST
// be permitted to manage any Server.
permit (
    principal is Operator,
    action == Action::"manage",
    resource is Server
)
when {
    context.clientIp.isIpv6()
    && context.clientIp.isInRange(ip("2001:db8:1::/64"))
};
