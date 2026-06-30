// FLOOR_USER_INTERNAL for `delete`.
permit (
    principal is User,
    action == Action::"delete",
    resource is Resource
)
when {
    principal.role == "user"
    && principal.isContractor == false
    && resource.classification == "internal"
};
