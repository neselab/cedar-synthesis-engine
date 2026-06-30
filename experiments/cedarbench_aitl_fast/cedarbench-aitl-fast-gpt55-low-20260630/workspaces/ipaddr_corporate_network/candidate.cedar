permit (
    principal is Employee,
    action == Action::"access",
    resource is InternalSystem
)
when {
    (
        context.sourceIp.isInRange(ip("10.0.0.0/8")) ||
        context.sourceIp.isInRange(ip("172.16.0.0/12")) ||
        context.sourceIp.isInRange(ip("192.168.0.0/16"))
    ) &&
    !context.sourceIp.isInRange(ip("10.50.0.0/16")) &&
    (
        !resource.requiresVpn ||
        context.sourceIp.isInRange(ip("10.10.0.0/16"))
    )
};

permit (
    principal is Employee,
    action == Action::"configure",
    resource is InternalSystem
)
when {
    (
        principal.role == "ops" ||
        principal.role == "admin"
    ) &&
    context.sourceIp.isInRange(ip("10.20.0.0/24")) &&
    !context.sourceIp.isInRange(ip("10.50.0.0/16"))
};

permit (
    principal is Employee,
    action == Action::"emergencyAccess",
    resource is InternalSystem
)
when {
    principal.role == "admin"
};