// Floor: a principal in the admins group MUST be able to view any document.
permit (
    principal is User,
    action == Action::"view",
    resource is Document
)
when {
    principal in [Group::"admins", Group::"auditors", Group::"compliance"]
};
