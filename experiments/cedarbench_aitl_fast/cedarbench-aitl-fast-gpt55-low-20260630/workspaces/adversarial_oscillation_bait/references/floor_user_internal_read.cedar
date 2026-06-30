// FLOOR_USER_INTERNAL for `read`. Non-contractor user MUST read
// internal resources.
permit (
    principal is User,
    action == Action::"read",
    resource is Resource
)
when {
    principal.role == "user"
    && principal.isContractor == false
    && resource.classification == "internal"
};
