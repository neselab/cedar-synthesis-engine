permit (
    principal is User,
    action == Action::"use",
    resource is Feature
)
when {
    resource.isEnabled == true &&
    (
        principal.role == "beta_tester" ||
        principal.role == "admin" ||
        principal.rolloutBucket < resource.rolloutPercentage
    )
};

permit (
    principal is User,
    action == Action::"preview",
    resource is Feature
)
when {
    principal.role == "beta_tester" ||
    principal.role == "admin"
};

permit (
    principal is User,
    action == Action::"configure",
    resource is Feature
)
when {
    principal.role == "admin"
};