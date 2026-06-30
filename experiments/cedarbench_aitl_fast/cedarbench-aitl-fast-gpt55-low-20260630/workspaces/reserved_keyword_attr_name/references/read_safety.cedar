// Ceiling: read only when member OR (public and hasAccess).
permit (principal is Member, action == Action::"read", resource is Channel)
when {
    resource.members.contains(principal) ||
    (resource.isPublic && principal.hasAccess)
};
