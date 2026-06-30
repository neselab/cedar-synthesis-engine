// Floor: a releaseManager MUST be permitted to approve.
// (No global forbids to exclude per section 8.8.)
permit (
    principal is PipelineUser,
    action == Action::"approve",
    resource is Deployment
)
when {
    principal.role == "releaseManager"
};
