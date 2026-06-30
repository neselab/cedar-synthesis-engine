// Ceiling: any tenant can delete.
permit (
    principal is Tenant,
    action == Action::"delete",
    resource is Resource
);
