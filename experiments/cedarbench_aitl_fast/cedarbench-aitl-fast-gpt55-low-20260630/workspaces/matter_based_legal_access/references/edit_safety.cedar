// Ceiling: edit permitted only when the user is assigned to the
// document's matter AND role is associate or partner AND (the
// document is not privileged OR the user is a partner).
permit (
    principal is User,
    action == Action::"edit",
    resource is Document
)
when {
    principal.assignedMatters.contains(resource.matter)
    && (principal.role == "associate" || principal.role == "partner")
    && (!resource.isPrivileged || principal.role == "partner")
};
