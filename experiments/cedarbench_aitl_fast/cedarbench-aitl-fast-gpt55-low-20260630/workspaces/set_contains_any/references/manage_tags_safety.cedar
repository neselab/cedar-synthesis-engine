// Ceiling: manageTags permitted only when owner.
permit (
    principal is User,
    action == Action::"manageTags",
    resource is Document
)
when {
    principal == resource.owner
};
