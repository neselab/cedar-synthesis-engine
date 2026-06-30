// Floor: the creator MUST be able to read EVEN WHEN they are no
// longer the current owner. This is a stronger version of
// floor_creator_read that explicitly exercises the post-transfer
// case where creator != currentOwner. A synthesizer that wrote
// "principal == resource.currentOwner" alone fails this floor; a
// synthesizer that wrote "principal == resource.creator &&
// principal == resource.currentOwner" (a misread of the joint
// invariant) also fails.
permit (
    principal is User,
    action == Action::"read",
    resource is File
)
when {
    principal == resource.creator &&
    principal != resource.currentOwner
};
