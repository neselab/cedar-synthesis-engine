// Floor: a supervisor with zone "all" MUST be permitted to inspect any item
// regardless of the item's zone.
permit (
    principal is Worker,
    action == Action::"inspect",
    resource is Inventory
)
when {
    principal.role == "supervisor"
    && principal.zone == "all"
};
