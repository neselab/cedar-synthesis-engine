// Ceiling: connect is permitted only when client is in a corporate
// range (IPv4 10.0.0.0/8 OR IPv6 2001:db8::/48) AND the server is
// either loopback or in the same address family as the client.
permit (
    principal is Operator,
    action == Action::"connect",
    resource is Server
)
when {
    (context.clientIp.isInRange(ip("10.0.0.0/8"))
     || context.clientIp.isInRange(ip("2001:db8::/48")))
    && (resource.serverIp.isLoopback()
        || (context.clientIp.isIpv4() && resource.serverIp.isIpv4())
        || (context.clientIp.isIpv6() && resource.serverIp.isIpv6()))
};
