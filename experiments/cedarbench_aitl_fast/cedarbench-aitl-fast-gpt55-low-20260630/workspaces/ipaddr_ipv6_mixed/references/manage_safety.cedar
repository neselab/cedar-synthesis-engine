// Ceiling: manage is permitted only when the client is in the family-
// appropriate admin subnet — IPv4 10.20.0.0/24 or IPv6 2001:db8:1::/64.
permit (
    principal is Operator,
    action == Action::"manage",
    resource is Server
)
when {
    (context.clientIp.isIpv4() && context.clientIp.isInRange(ip("10.20.0.0/24")))
    || (context.clientIp.isIpv6() && context.clientIp.isInRange(ip("2001:db8:1::/64")))
};
