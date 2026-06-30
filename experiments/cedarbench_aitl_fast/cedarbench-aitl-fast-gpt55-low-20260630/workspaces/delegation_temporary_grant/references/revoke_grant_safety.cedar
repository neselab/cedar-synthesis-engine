// Ceiling: revokeGrant permitted only when principal is the owner.
permit (
    principal is User,
    action == Action::"revokeGrant",
    resource is Resource
)
when {
    principal == resource.owner
};
