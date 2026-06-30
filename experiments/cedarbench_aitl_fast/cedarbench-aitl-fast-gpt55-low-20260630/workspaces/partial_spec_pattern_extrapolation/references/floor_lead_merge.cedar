// Floor: a lead_dev MUST be permitted to merge any CodeArtifact.
// This is one of the two permissions extrapolated from the spec's
// "extends senior_dev with merge + manageBranches" delta.
permit (
    principal is Developer,
    action == Action::"merge",
    resource is CodeArtifact
)
when {
    principal.role == "lead_dev"
};
