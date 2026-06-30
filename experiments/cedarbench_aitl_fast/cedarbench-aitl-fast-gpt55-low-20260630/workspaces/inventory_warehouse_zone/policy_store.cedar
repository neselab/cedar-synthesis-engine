// Policy store — verified policies appended here

// --- Verified (eval iteration 1) ---
permit (
    principal is Worker,
    action == Action::"move",
    resource is Inventory
)
when {
    (principal.zone == resource.currentZone || principal.zone == "all") &&
    (resource.isHazardous == false || principal.role == "supervisor")
};

permit (
    principal is Worker,
    action == Action::"inspect",
    resource is Inventory
)
when {
    principal.zone == resource.currentZone || principal.zone == "all"
};

permit (
    principal is Worker,
    action == Action::"dispose",
    resource is Inventory
)
when {
    principal.role == "supervisor" &&
    (principal.zone == resource.currentZone || principal.zone == "all")
};
