// Floor: a beta tester MUST be permitted to preview any feature.
// No global forbids in this scenario, so no exclusions needed (S8.8).
permit (
    principal is User,
    action == Action::"preview",
    resource is Feature
)
when {
    principal.role == "beta_tester"
};
