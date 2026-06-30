// Floor: a handler in the same zone MUST be permitted to inspect any item
// (no role restriction on inspect).
permit (
    principal is Worker,
    action == Action::"inspect",
    resource is Inventory
)
when {
    principal.role == "handler"
    && principal.zone == resource.currentZone
};
