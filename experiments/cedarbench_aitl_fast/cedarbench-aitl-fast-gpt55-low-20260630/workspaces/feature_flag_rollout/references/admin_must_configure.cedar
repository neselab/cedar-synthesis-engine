// Floor: an admin MUST be permitted to configure any feature.
// No global forbids in this scenario, so no exclusions needed (S8.8).
permit (
    principal is User,
    action == Action::"configure",
    resource is Feature
)
when {
    principal.role == "admin"
};
