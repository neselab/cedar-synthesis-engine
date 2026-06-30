// Floor: a user in groupA MUST be permitted to access alpha resources.
permit (principal is User, action == Action::"access", resource is Resource)
when {
    principal.groupA && resource.category == "alpha"
};
