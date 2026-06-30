// Floor: a supervisor in the same zone MUST be permitted to dispose of
// any item (hazardous or not).
permit (
    principal is Worker,
    action == Action::"dispose",
    resource is Inventory
)
when {
    principal.role == "supervisor"
    && principal.zone == resource.currentZone
};
