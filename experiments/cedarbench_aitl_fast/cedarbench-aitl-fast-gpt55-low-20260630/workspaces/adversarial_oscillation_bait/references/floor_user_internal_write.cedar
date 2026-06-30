// FLOOR_USER_INTERNAL for `write`.
permit (
    principal is User,
    action == Action::"write",
    resource is Resource
)
when {
    principal.role == "user"
    && principal.isContractor == false
    && resource.classification == "internal"
};
