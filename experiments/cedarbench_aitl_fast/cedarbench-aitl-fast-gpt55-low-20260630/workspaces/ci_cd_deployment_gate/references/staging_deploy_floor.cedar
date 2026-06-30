// Floor: a lead with passing tests MUST be permitted to deploy
// to staging. (No global forbids to exclude per section 8.8.)
permit (
    principal is PipelineUser,
    action == Action::"deploy",
    resource is Deployment
)
when {
    principal.role == "lead"
    && resource.environment == "staging"
    && resource.hasPassedTests
};
