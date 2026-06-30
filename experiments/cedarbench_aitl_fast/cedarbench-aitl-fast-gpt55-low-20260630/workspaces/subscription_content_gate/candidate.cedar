permit (
    principal is Subscriber,
    action == Action::"stream",
    resource is Content
)
when {
    principal.isActive == true &&
    (
        resource.isPreview == true ||
        resource.tier == "free" ||
        (resource.tier == "basic" && (principal.plan == "basic" || principal.plan == "premium")) ||
        (resource.tier == "premium" && principal.plan == "premium")
    )
};

permit (
    principal is Subscriber,
    action == Action::"download",
    resource is Content
)
when {
    principal.isActive == true &&
    (
        principal.plan == "basic" ||
        principal.plan == "premium"
    ) &&
    (
        resource.tier == "free" ||
        (resource.tier == "basic" && (principal.plan == "basic" || principal.plan == "premium")) ||
        (resource.tier == "premium" && principal.plan == "premium")
    )
};

permit (
    principal is Subscriber,
    action == Action::"share",
    resource is Content
)
when {
    principal.isActive == true &&
    principal.plan == "premium"
};