// Floor: any User must be able to read files matching docs/*.
permit (
    principal is User,
    action == Action::"read",
    resource is File
)
when {
    resource.path like "docs/*"
};
