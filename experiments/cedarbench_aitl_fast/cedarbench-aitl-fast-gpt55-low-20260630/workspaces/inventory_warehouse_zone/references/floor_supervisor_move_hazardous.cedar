// Floor: a supervisor in the same zone MUST be permitted to move a
// hazardous item. (§8.8: role == "supervisor" satisfies the hazardous
// escalation condition in the move ceiling.)
permit (
    principal is Worker,
    action == Action::"move",
    resource is Inventory
)
when {
    principal.role == "supervisor"
    && principal.zone == resource.currentZone
    && resource.isHazardous == true
};
