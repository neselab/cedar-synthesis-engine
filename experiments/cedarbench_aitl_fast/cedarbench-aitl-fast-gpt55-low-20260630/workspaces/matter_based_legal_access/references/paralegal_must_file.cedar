// Floor: a paralegal assigned to the matter MUST be permitted to
// file a non-privileged document in that matter.
permit (
    principal is User,
    action == Action::"file",
    resource is Document
)
when {
    principal.role == "paralegal"
    && principal.assignedMatters.contains(resource.matter)
    && !resource.isPrivileged
};
