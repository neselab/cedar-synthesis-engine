// Ceiling: move permitted only when zone matches (or worker zone is "all")
// AND the item is non-hazardous OR the worker is a supervisor.
permit (
    principal is Worker,
    action == Action::"move",
    resource is Inventory
)
when {
    (principal.zone == resource.currentZone || principal.zone == "all")
    && (resource.isHazardous == false || principal.role == "supervisor")
};
