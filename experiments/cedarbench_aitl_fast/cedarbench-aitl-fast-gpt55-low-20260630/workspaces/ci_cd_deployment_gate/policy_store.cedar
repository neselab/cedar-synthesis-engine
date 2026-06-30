// Policy store — verified policies appended here

// --- Verified (eval iteration 1) ---
permit (
    principal is PipelineUser,
    action == Action::"deploy",
    resource is Deployment
)
when {
    resource.hasPassedTests == true &&
    (
        resource.environment == "dev" ||
        (
            resource.environment == "staging" &&
            (principal.role == "lead" || principal.role == "releaseManager")
        ) ||
        (
            resource.environment == "production" &&
            principal.role == "releaseManager"
        )
    )
};

permit (
    principal is PipelineUser,
    action == Action::"rollback",
    resource is Deployment
)
when {
    principal.role == "lead" || principal.role == "releaseManager"
};

permit (
    principal is PipelineUser,
    action == Action::"approve",
    resource is Deployment
)
when {
    principal.role == "releaseManager"
};
