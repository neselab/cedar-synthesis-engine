// Floor: an Operator on the IPv4 admin subnet (10.20.0.0/24) MUST be
// permitted to manage any Server.
permit (
    principal is Operator,
    action == Action::"manage",
    resource is Server
)
when {
    context.clientIp.isIpv4()
    && context.clientIp.isInRange(ip("10.20.0.0/24"))
};
