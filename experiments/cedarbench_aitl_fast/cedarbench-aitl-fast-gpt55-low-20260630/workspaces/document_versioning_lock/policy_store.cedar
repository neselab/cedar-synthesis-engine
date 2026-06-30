// Policy store — verified policies appended here

// --- Verified (eval iteration 1) ---
permit (
    principal is User,
    action == Action::"read",
    resource is Document
);

permit (
    principal is User,
    action == Action::"edit",
    resource is Document
)
when {
    (principal.role == "editor" || principal.role == "admin") &&
    (!resource.isLocked || resource.lockedBy == principal)
};

permit (
    principal is User,
    action == Action::"lock",
    resource is Document
)
when {
    principal.role == "editor" || principal.role == "admin"
};

permit (
    principal is User,
    action == Action::"unlock",
    resource is Document
)
when {
    principal == resource.lockedBy || principal.role == "admin"
};

permit (
    principal is User,
    action == Action::"publish",
    resource is Document
)
when {
    principal.role == "admin" &&
    resource.isDraft
};
