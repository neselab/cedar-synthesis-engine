// Floor: a lead MUST be permitted to rollback any environment.
// (No global forbids to exclude per section 8.8.)
permit (
    principal is PipelineUser,
    action == Action::"rollback",
    resource is Deployment
)
when {
    principal.role == "lead"
};
