// Floor: any User MUST be permitted to read a public resource.
permit (
    principal is User,
    action == Action::"readResource",
    resource is Resource
)
when {
    resource.classification == "public"
};
