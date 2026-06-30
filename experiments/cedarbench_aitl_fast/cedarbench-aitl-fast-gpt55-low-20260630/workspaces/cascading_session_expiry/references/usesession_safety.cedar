// Ceiling: useSession is permitted only when context.now is strictly
// before BOTH the parent and the self expiry. Equivalent to
// context.now < min(parentExpiresAt, selfExpiresAt).
permit (
    principal is User,
    action == Action::"useSession",
    resource is Resource
)
when {
    context.now < context.session.parentExpiresAt
    && context.now < context.session.selfExpiresAt
};
