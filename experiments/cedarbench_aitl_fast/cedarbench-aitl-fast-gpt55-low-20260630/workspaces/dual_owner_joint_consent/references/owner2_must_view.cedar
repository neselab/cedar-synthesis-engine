// Floor: owner2 MUST be permitted to view their joint asset. No
// context preconditions on view.
permit (
    principal is User,
    action == Action::"view",
    resource is JointAsset
)
when {
    principal == resource.owner2
};
