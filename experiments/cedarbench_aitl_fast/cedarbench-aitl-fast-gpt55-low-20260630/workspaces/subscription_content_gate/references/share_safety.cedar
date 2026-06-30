// Ceiling: share permitted only when subscriber is active AND
// plan is premium. No content-tier restriction for sharing.
permit (
    principal is Subscriber,
    action == Action::"share",
    resource is Content
)
when {
    principal.isActive
    && principal.plan == "premium"
};
