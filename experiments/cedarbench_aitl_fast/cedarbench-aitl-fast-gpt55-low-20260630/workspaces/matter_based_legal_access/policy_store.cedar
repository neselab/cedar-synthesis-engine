// Policy store — verified policies appended here

// --- Verified (eval iteration 1) ---
permit (
    principal is User,
    action == Action::"view",
    resource is Document
)
when {
    principal.assignedMatters.contains(resource.matter) &&
    (
        resource.isPrivileged == false ||
        principal.role == "partner"
    )
};

permit (
    principal is User,
    action == Action::"edit",
    resource is Document
)
when {
    principal.assignedMatters.contains(resource.matter) &&
    (
        principal.role == "associate" ||
        principal.role == "partner"
    ) &&
    (
        resource.isPrivileged == false ||
        principal.role == "partner"
    )
};

permit (
    principal is User,
    action == Action::"file",
    resource is Document
)
when {
    principal.assignedMatters.contains(resource.matter) &&
    (
        resource.isPrivileged == false ||
        principal.role == "partner"
    )
};

permit (
    principal is User,
    action == Action::"redact",
    resource is Document
)
when {
    principal.assignedMatters.contains(resource.matter) &&
    principal.role == "partner"
};
