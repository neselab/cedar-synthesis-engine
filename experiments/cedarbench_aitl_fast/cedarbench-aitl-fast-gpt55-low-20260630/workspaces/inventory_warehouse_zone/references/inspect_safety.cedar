// Ceiling: inspect permitted only when zone matches or worker zone is "all".
permit (
    principal is Worker,
    action == Action::"inspect",
    resource is Inventory
)
when {
    principal.zone == resource.currentZone || principal.zone == "all"
};
