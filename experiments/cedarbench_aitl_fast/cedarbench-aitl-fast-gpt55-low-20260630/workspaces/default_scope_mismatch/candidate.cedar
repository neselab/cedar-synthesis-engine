forbid (
    principal,
    action in [Action::"read", Action::"write"],
    resource
)
when {
    principal is User &&
    resource is Document &&
    principal.tenant != resource.tenant
};

permit (
    principal,
    action == Action::"read",
    resource
)
when {
    principal is User &&
    resource is Document &&
    principal.tenant == resource.tenant &&
    principal.tenant.defaultDeny == false
};

permit (
    principal,
    action == Action::"read",
    resource
)
when {
    principal is User &&
    resource is Document &&
    principal.tenant == resource.tenant &&
    principal.role == "admin"
};

permit (
    principal,
    action == Action::"write",
    resource
)
when {
    principal is User &&
    resource is Document &&
    principal.tenant == resource.tenant &&
    principal.role == "admin"
};