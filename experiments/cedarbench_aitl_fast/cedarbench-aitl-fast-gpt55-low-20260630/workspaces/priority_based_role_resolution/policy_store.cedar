// Policy store — verified policies appended here

// --- Verified (eval iteration 1) ---
permit (
    principal is User,
    action == Action::"viewRecord",
    resource is Record
)
when {
    resource.tier == "public"
    && (
        principal.roles.contains("guest")
        || principal.roles.contains("subscriber")
        || principal.roles.contains("premium")
        || principal.roles.contains("admin")
    )
};

permit (
    principal is User,
    action == Action::"viewRecord",
    resource is Record
)
when {
    resource.tier == "confidential"
    && (
        principal.roles.contains("subscriber")
        || principal.roles.contains("premium")
        || principal.roles.contains("admin")
    )
};

permit (
    principal is User,
    action == Action::"viewRecord",
    resource is Record
)
when {
    resource.tier == "premium-only"
    && (
        principal.roles.contains("premium")
        || principal.roles.contains("admin")
    )
};

permit (
    principal is User,
    action == Action::"viewRecord",
    resource is Record
)
when {
    resource.tier == "admin-only"
    && principal.roles.contains("admin")
};

permit (
    principal is User,
    action == Action::"editRecord",
    resource is Record
)
when {
    principal.roles.contains("admin")
};

permit (
    principal is User,
    action == Action::"deleteRecord",
    resource is Record
)
when {
    principal.roles.contains("admin")
};
