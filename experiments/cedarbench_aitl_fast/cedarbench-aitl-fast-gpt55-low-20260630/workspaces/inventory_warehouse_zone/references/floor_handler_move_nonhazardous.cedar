// Floor: a handler in the same zone MUST be permitted to move a
// non-hazardous item.
permit (
    principal is Worker,
    action == Action::"move",
    resource is Inventory
)
when {
    principal.role == "handler"
    && principal.zone == resource.currentZone
    && resource.isHazardous == false
};
