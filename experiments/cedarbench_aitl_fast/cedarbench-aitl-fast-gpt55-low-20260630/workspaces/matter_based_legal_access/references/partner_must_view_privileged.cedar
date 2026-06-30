// Floor: a partner assigned to the matter MUST be permitted to view
// a privileged document in that matter.
permit (
    principal is User,
    action == Action::"view",
    resource is Document
)
when {
    principal.role == "partner"
    && principal.assignedMatters.contains(resource.matter)
    && resource.isPrivileged
};
