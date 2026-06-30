// Floor: a lead (level 3) MUST be permitted to execute restrictedAction resources.
permit (
    principal is Employee,
    action == Action::"execute",
    resource is Resource
)
when {
    principal.level == 3 && resource.category == "restrictedAction"
};
