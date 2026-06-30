// Ceiling: stream permitted only when subscriber is active AND
// EITHER the content is a preview OR the subscriber's plan
// dominates the content's tier.
// Tier hierarchy: free < basic < premium.
permit (
    principal is Subscriber,
    action == Action::"stream",
    resource is Content
)
when {
    principal.isActive
    && (
        resource.isPreview
        || resource.tier == "free"
        || (resource.tier == "basic" && (principal.plan == "basic" || principal.plan == "premium"))
        || (resource.tier == "premium" && principal.plan == "premium")
    )
};
