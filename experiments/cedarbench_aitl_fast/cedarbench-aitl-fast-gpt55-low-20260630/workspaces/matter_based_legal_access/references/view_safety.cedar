// Ceiling: view permitted only when the user is assigned to the
// document's matter AND (the document is not privileged OR the user
// is a partner).
permit (
    principal is User,
    action == Action::"view",
    resource is Document
)
when {
    principal.assignedMatters.contains(resource.matter)
    && (!resource.isPrivileged || principal.role == "partner")
};
