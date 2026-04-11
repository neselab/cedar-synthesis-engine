// Ceiling: createGrant permitted only when principal is the owner.
// Grantees cannot create grants for others; grant management is strictly
// owner-only.
permit (
    principal is User,
    action == Action::"createGrant",
    resource is Resource
)
when {
    principal == resource.owner
};
