// Floor: a developer with passing tests MUST be permitted to deploy
// to dev. (No global forbids to exclude per section 8.8.)
permit (
    principal is PipelineUser,
    action == Action::"deploy",
    resource is Deployment
)
when {
    principal.role == "developer"
    && resource.environment == "dev"
    && resource.hasPassedTests
};
