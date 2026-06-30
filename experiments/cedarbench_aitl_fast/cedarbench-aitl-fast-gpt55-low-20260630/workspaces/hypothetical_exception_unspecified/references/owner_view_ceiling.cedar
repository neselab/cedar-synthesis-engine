// Ceiling: viewProfile is permitted ONLY when principal == resource.owner.
// No extra conditions — the spec's hedging language ("normally", "rare
// exceptions handled separately by the security team") does NOT
// authorize any in-policy exception attribute. Any candidate that adds
// `&& !context.<invented>` will be more restrictive than this ceiling
// and will fail the floor.
permit (
    principal is User,
    action == Action::"viewProfile",
    resource is Profile
)
when {
    principal == resource.owner
};
