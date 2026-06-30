// Policy store — verified policies appended here

// --- Verified (eval iteration 1) ---
permit (
    principal is User,
    action == Action::"view",
    resource is Secret
)
when {
    resource.sensitivityLevel == 1
};

permit (
    principal is User,
    action == Action::"view",
    resource is Secret
)
when {
    resource.sensitivityLevel == 2 &&
    context.hasMfa
};

permit (
    principal is User,
    action == Action::"view",
    resource is Secret
)
when {
    resource.sensitivityLevel == 3 &&
    context.hasMfa &&
    context.hasManagerApproval
};

permit (
    principal is User,
    action == Action::"rotate",
    resource is Secret
)
when {
    (principal.role == "security_officer" || principal.role == "admin") &&
    (resource.sensitivityLevel == 1 || resource.sensitivityLevel == 2) &&
    context.hasMfa
};

permit (
    principal is User,
    action == Action::"rotate",
    resource is Secret
)
when {
    (principal.role == "security_officer" || principal.role == "admin") &&
    resource.sensitivityLevel == 3 &&
    context.hasMfa &&
    context.hasSecurityReview
};

permit (
    principal is User,
    action == Action::"revoke",
    resource is Secret
)
when {
    principal.role == "admin" &&
    context.hasMfa &&
    context.hasManagerApproval
};
