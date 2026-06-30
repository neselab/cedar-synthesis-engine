// Floor: a member with "pin" capability AND "pinning" affinity MUST be permitted to pin.
permit (principal is Member, action == Action::"pin", resource is Channel)
when {
    resource.members.contains(principal) &&
    principal.permits.contains("pin") &&
    principal.likedItems.contains("pinning")
};
