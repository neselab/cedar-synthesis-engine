// Floor: an active free-plan subscriber MUST be able to stream
// preview content. Ensures the preview bypass works for the
// lowest-tier plan.
permit (
    principal is Subscriber,
    action == Action::"stream",
    resource is Content
)
when {
    principal.isActive
    && principal.plan == "free"
    && resource.isPreview
};
