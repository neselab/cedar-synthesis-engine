// Ceiling: view permitted only when principal is in a privileged group,
// OR the document owner is in a privileged group, OR principal is owner.
permit (
    principal is User,
    action == Action::"view",
    resource is Document
)
when {
    principal in [Group::"admins", Group::"auditors", Group::"compliance"]
    || resource.owner in [Group::"admins", Group::"auditors", Group::"compliance"]
    || principal == resource.owner
};
