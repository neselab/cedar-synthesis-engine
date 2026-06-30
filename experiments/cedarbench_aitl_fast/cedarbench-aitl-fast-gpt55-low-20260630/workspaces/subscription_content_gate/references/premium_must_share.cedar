// Floor: an active premium subscriber MUST be able to share
// content. Tests that premium plan unlocks the share action.
permit (
    principal is Subscriber,
    action == Action::"share",
    resource is Content
)
when {
    principal.isActive
    && principal.plan == "premium"
};
