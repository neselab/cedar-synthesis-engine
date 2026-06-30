// Ceiling: delegate permitted only when principal is the resource
// owner. NO grant — even a valid depth-1 grant — confers the
// authority to re-delegate. This is the anti-transitivity guarantee:
// chains cannot extend themselves.
permit (
    principal is User,
    action == Action::"delegate",
    resource is Resource
)
when {
    principal == resource.owner
};
