// Floor: an associate assigned to the matter MUST be permitted to
// edit a non-privileged document in that matter.
permit (
    principal is User,
    action == Action::"edit",
    resource is Document
)
when {
    principal.role == "associate"
    && principal.assignedMatters.contains(resource.matter)
    && !resource.isPrivileged
};
