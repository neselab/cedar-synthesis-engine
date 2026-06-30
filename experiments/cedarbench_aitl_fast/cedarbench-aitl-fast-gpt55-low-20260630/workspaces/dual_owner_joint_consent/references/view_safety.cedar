// Ceiling: view permitted ONLY for the two co-owners. No context
// requirement — either owner may read at any time.
permit (
    principal is User,
    action == Action::"view",
    resource is JointAsset
)
when {
    principal == resource.owner1
    || principal == resource.owner2
};
