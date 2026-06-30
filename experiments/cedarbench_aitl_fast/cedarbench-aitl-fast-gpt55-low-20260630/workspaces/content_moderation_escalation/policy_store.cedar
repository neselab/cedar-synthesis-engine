// Policy store — verified policies appended here

// --- Verified (eval iteration 1) ---
permit (
    principal is Moderator,
    action == Action::"review",
    resource is ContentReport
)
when {
    (principal.trustLevel >= 1 && resource.severity <= 2) ||
    (principal.trustLevel >= 2 && resource.severity <= 4) ||
    (principal.trustLevel >= 3)
};

permit (
    principal is Moderator,
    action == Action::"resolve",
    resource is ContentReport
)
when {
    (principal.trustLevel >= 1 && resource.severity <= 2) ||
    (principal.trustLevel >= 2 && resource.severity <= 4) ||
    (principal.trustLevel >= 3)
};

permit (
    principal is Moderator,
    action == Action::"escalate",
    resource is ContentReport
);

permit (
    principal is Moderator,
    action == Action::"override",
    resource is ContentReport
)
when {
    principal.trustLevel >= 3
};
