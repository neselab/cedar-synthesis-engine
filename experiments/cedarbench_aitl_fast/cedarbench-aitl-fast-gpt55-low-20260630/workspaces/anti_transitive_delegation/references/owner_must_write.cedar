// Floor: the resource owner MUST be permitted to write their own
// resource. (No grant lookup required.)
permit (
    principal is User,
    action == Action::"write",
    resource is Resource
)
when {
    principal == resource.owner
};
