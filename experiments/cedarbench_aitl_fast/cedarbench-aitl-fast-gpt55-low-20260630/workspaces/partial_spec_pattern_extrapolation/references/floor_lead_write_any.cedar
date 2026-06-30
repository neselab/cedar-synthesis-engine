// Floor: a lead_dev MUST be permitted to write any CodeArtifact
// (this permission is inherited from senior_dev, asserting the
// extrapolation went through).
permit (
    principal is Developer,
    action == Action::"write",
    resource is CodeArtifact
)
when {
    principal.role == "lead_dev"
};
