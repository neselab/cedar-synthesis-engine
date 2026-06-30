// Floor: a user in groupB MUST be permitted to access beta resources.
permit (principal is User, action == Action::"access", resource is Resource)
when {
    principal.groupB && resource.category == "beta"
};
