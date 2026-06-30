// Ceiling: use permitted only when feature isEnabled AND
// (role == "beta_tester" OR role == "admin" OR rolloutBucket < rolloutPercentage).
permit (
    principal is User,
    action == Action::"use",
    resource is Feature
)
when {
    resource.isEnabled
    && (principal.role == "beta_tester"
        || principal.role == "admin"
        || principal.rolloutBucket < resource.rolloutPercentage)
};
