// Ceiling: rollback permitted only when the user is a lead or
// releaseManager. No test-pass requirement (emergency action).
permit (
    principal is PipelineUser,
    action == Action::"rollback",
    resource is Deployment
)
when {
    principal.role == "lead"
    || principal.role == "releaseManager"
};
