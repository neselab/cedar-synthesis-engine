// Policy store — verified policies appended here

// --- Verified (eval iteration 1) ---
permit (
    principal is User,
    action == Action::"edit",
    resource is Document
)
when {
    principal.role == "editor"
};

permit (
    principal is User,
    action == Action::"edit",
    resource is Document
)
when {
    principal == resource.owner
};
