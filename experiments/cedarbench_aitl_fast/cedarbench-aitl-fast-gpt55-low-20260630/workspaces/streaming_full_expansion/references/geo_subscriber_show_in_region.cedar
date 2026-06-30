// Ceiling: Subscriber may watch a Show only when in the show's allowedRegions.
permit (
    principal is Subscriber,
    action == Action::"watch",
    resource is Show
)
when {
    resource.allowedRegions.contains(context.region)
};
