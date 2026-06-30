// Floor: a partner assigned to the matter MUST be permitted to
// redact a document in that matter. Since only partners can redact,
// this uses a non-privileged document to avoid entangling with the
// privileged gate (though partners satisfy it regardless).
permit (
    principal is User,
    action == Action::"redact",
    resource is Document
)
when {
    principal.role == "partner"
    && principal.assignedMatters.contains(resource.matter)
    && !resource.isPrivileged
};
