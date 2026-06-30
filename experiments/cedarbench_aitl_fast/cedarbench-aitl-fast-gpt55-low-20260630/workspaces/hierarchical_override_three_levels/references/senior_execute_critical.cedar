// Floor: a senior (level 2) MUST be permitted to execute criticalAction resources.
permit (
    principal is Employee,
    action == Action::"execute",
    resource is Resource
)
when {
    principal.level == 2 && resource.category == "criticalAction"
};
