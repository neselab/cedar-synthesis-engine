// Ceiling: dispose permitted only when supervisor AND zone matches (or "all").
permit (
    principal is Worker,
    action == Action::"dispose",
    resource is Inventory
)
when {
    principal.role == "supervisor"
    && (principal.zone == resource.currentZone || principal.zone == "all")
};
