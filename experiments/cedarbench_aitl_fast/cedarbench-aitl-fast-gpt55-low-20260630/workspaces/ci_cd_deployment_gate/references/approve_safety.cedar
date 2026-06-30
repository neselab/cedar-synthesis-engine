// Ceiling: approve permitted only when the user is a releaseManager.
permit (
    principal is PipelineUser,
    action == Action::"approve",
    resource is Deployment
)
when {
    principal.role == "releaseManager"
};
