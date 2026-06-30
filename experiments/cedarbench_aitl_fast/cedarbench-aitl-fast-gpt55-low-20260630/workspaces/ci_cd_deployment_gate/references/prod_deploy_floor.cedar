// Floor: a releaseManager with passing tests MUST be permitted to
// deploy to production. (No global forbids to exclude per section 8.8.)
permit (
    principal is PipelineUser,
    action == Action::"deploy",
    resource is Deployment
)
when {
    principal.role == "releaseManager"
    && resource.environment == "production"
    && resource.hasPassedTests
};
