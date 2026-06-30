// Ceiling: deploy permitted only when tests passed AND the
// environment-specific role gate is satisfied:
//   dev       -> any role
//   staging   -> lead or releaseManager
//   production -> releaseManager only
permit (
    principal is PipelineUser,
    action == Action::"deploy",
    resource is Deployment
)
when {
    resource.hasPassedTests
    && (
        resource.environment == "dev"
        || (resource.environment == "staging"
            && (principal.role == "lead"
                || principal.role == "releaseManager"))
        || (resource.environment == "production"
            && principal.role == "releaseManager")
    )
};
