// Floor: viewProfile MUST be permitted whenever principal == resource.owner.
// No exclusions — there are no global forbids in this spec, and the
// hedging language does not define any concrete exception condition.
// A candidate that adds `&& !context.<invented>` will be MORE
// restrictive than this floor, violating it.
permit (
    principal is User,
    action == Action::"viewProfile",
    resource is Profile
)
when {
    principal == resource.owner
};
