// Floor: any worker MUST be able to view any material.
permit (
    principal is Worker,
    action == Action::"view",
    resource is Material
);
