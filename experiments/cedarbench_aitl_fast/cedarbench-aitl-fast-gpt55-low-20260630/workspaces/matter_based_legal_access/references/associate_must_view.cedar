// Floor: an associate assigned to the matter MUST be permitted to
// view a non-privileged document in that matter.
permit (
    principal is User,
    action == Action::"view",
    resource is Document
)
when {
    principal.role == "associate"
    && principal.assignedMatters.contains(resource.matter)
    && !resource.isPrivileged
};
