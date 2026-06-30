// Policy store — verified policies appended here

// --- Verified (eval iteration 1) ---
permit (
    principal is User,
    action == Action::"access",
    resource is Resource
)
when {
    principal.tenantId == resource.tenantId
};
