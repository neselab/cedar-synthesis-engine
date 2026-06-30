// Ceiling: execute permitted only when level is high enough for the category.
// - standard: level >= 1
// - criticalAction: level >= 2
// - restrictedAction: level >= 3 (the override — senior CANNOT execute)
permit (
    principal is Employee,
    action == Action::"execute",
    resource is Resource
)
when {
    (principal.level >= 1 && resource.category == "standard")
    || (principal.level >= 2 && resource.category == "criticalAction")
    || (principal.level >= 3 && resource.category == "restrictedAction")
};
