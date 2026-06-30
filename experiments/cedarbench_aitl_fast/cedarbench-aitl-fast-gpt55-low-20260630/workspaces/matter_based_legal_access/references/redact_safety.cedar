// Ceiling: redact permitted only when the user is assigned to the
// document's matter AND role is partner. Partners satisfy the
// privileged-document gate automatically, so no separate isPrivileged
// check is needed.
permit (
    principal is User,
    action == Action::"redact",
    resource is Document
)
when {
    principal.assignedMatters.contains(resource.matter)
    && principal.role == "partner"
};
