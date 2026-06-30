// Floor: a junior (level 1) MUST be permitted to read standard resources.
permit (
    principal is Employee,
    action == Action::"read",
    resource is Resource
)
when {
    principal.level == 1 && resource.category == "standard"
};
