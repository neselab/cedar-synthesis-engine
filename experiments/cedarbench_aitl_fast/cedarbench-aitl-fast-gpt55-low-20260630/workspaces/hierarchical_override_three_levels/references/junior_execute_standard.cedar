// Floor: a junior (level 1) MUST be permitted to execute standard resources.
permit (
    principal is Employee,
    action == Action::"execute",
    resource is Resource
)
when {
    principal.level == 1 && resource.category == "standard"
};
