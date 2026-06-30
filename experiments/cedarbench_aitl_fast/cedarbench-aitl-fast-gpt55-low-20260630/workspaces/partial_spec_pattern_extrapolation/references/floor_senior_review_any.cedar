// Floor: a senior_dev MUST be permitted to review any CodeArtifact.
permit (
    principal is Developer,
    action == Action::"review",
    resource is CodeArtifact
)
when {
    principal.role == "senior_dev"
};
