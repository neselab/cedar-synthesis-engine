// Floor: an active basic-plan subscriber MUST be able to download
// free-tier content. Tests that basic plan can download and that
// plan dominance works for download action.
permit (
    principal is Subscriber,
    action == Action::"download",
    resource is Content
)
when {
    principal.isActive
    && principal.plan == "basic"
    && resource.tier == "free"
};
