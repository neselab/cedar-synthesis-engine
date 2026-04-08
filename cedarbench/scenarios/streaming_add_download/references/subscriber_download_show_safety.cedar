// Ceiling: Subscriber may download a Show only when the show is NOT free.
permit (
    principal is Subscriber,
    action == Action::"download",
    resource is Show
)
when {
    !resource.isFree
};
