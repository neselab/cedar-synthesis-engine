// Floor: a senior (level 2) MUST be permitted to read restrictedAction resources.
// (This is the "view but cannot execute" half of the override pattern.)
permit (
    principal is Employee,
    action == Action::"read",
    resource is Resource
)
when {
    principal.level == 2 && resource.category == "restrictedAction"
};
