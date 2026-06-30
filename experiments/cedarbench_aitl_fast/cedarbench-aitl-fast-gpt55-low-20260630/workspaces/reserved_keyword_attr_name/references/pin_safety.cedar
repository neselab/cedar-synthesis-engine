// Ceiling: pin only when member AND has "pin" capability AND has "pinning" affinity.
permit (principal is Member, action == Action::"pin", resource is Channel)
when {
    resource.members.contains(principal) &&
    principal.permits.contains("pin") &&
    principal.likedItems.contains("pinning")
};
