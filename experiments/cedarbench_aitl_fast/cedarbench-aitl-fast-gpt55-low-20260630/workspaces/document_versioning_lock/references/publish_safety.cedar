// Ceiling: publish is permitted only for admin AND document is draft.
permit (
    principal is User,
    action == Action::"publish",
    resource is Document
)
when {
    principal.role == "admin" && resource.isDraft
};
