// Floor: Subscriber MUST be permitted to download any non-free Show.
permit (
    principal is Subscriber,
    action == Action::"download",
    resource is Show
)
when {
    !resource.isFree
};
