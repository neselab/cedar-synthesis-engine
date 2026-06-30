// Ceiling: download permitted only when subscriber is active AND
// plan is basic or premium (free cannot download) AND subscriber's
// plan dominates the content's tier.
// Tier hierarchy: free < basic < premium.
permit (
    principal is Subscriber,
    action == Action::"download",
    resource is Content
)
when {
    principal.isActive
    && (principal.plan == "basic" || principal.plan == "premium")
    && (
        resource.tier == "free"
        || (resource.tier == "basic" && (principal.plan == "basic" || principal.plan == "premium"))
        || (resource.tier == "premium" && principal.plan == "premium")
    )
};
