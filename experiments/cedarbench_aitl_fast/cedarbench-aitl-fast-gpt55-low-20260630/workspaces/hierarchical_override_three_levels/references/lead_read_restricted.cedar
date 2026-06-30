// Floor: a lead (level 3) MUST be permitted to read restrictedAction resources.
permit (
    principal is Employee,
    action == Action::"read",
    resource is Resource
)
when {
    principal.level == 3 && resource.category == "restrictedAction"
};
