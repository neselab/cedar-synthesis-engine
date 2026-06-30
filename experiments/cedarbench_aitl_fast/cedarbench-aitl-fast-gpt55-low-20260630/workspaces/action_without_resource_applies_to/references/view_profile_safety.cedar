// Ceiling: viewProfile permitted only when the principal owns the profile.
// Contrasting case: this resourceful action's condition depends on the
// resource itself (resource.owner), not just on the principal.
permit (
    principal is User,
    action == Action::"viewProfile",
    resource is Profile
)
when {
    principal == resource.owner
};
