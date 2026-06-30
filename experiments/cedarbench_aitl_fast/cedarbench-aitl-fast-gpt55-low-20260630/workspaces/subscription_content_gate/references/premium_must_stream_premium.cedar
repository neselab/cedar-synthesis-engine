// Floor: an active premium subscriber MUST be able to stream
// premium-tier non-preview content. Tests that plan dominance
// works at the highest tier without relying on the preview bypass.
permit (
    principal is Subscriber,
    action == Action::"stream",
    resource is Content
)
when {
    principal.isActive
    && principal.plan == "premium"
    && resource.tier == "premium"
    && !resource.isPreview
};
