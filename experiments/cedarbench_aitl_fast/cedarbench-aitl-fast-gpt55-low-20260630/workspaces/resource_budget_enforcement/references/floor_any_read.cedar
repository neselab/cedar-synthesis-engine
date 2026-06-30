// Floor: any tenant MUST read.
permit (
    principal is Tenant,
    action == Action::"read",
    resource is Resource
);
