// Floor: the resource owner MUST be permitted to perform `delegate`
// on their own resource — this is how new grants get issued in the
// first place.
permit (
    principal is User,
    action == Action::"delegate",
    resource is Resource
)
when {
    principal == resource.owner
};
