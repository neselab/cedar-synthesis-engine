// Floor: a user whose rolloutBucket < rolloutPercentage MUST be
// permitted to use an enabled feature.
// No global forbids in this scenario, so no exclusions needed (S8.8).
permit (
    principal is User,
    action == Action::"use",
    resource is Feature
)
when {
    resource.isEnabled
    && principal.rolloutBucket < resource.rolloutPercentage
};
