// Ceiling: view is open — any worker may view any material.
// (View just exposes catalog metadata, not the material itself.)
permit (
    principal is Worker,
    action == Action::"view",
    resource is Material
);
