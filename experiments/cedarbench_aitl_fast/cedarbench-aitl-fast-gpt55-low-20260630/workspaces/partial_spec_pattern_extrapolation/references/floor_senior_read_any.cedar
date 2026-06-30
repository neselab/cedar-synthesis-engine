// Floor: a senior_dev MUST be permitted to read any CodeArtifact,
// regardless of project.
permit (
    principal is Developer,
    action == Action::"read",
    resource is CodeArtifact
)
when {
    principal.role == "senior_dev"
};
