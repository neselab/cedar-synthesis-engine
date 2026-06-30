// Ceiling: any tenant can read.
permit (
    principal is Tenant,
    action == Action::"read",
    resource is Resource
);
