// Ceiling: read permitted only when level is high enough for the category.
// - standard: level >= 1
// - criticalAction: level >= 2
// - restrictedAction: level >= 2 (senior CAN read restricted; cannot execute)
permit (
    principal is Employee,
    action == Action::"read",
    resource is Resource
)
when {
    (principal.level >= 1 && resource.category == "standard")
    || (principal.level >= 2 && resource.category == "criticalAction")
    || (principal.level >= 2 && resource.category == "restrictedAction")
};
