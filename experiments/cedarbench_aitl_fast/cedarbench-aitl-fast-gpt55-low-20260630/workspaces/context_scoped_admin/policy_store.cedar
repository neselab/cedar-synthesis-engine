// Policy store — verified policies appended here

// --- Verified (eval iteration 1) ---
permit (
    principal is User,
    action == Action::"view",
    resource is Resource
)
when {
    principal.adminOf.contains(resource.tenant)
};

permit (
    principal is User,
    action == Action::"modify",
    resource is Resource
)
when {
    principal.adminOf.contains(resource.tenant)
};

permit (
    principal is User,
    action == Action::"delete",
    resource is Resource
)
when {
    principal.adminOf.contains(resource.tenant)
};
