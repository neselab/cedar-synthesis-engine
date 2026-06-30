// Floor: Subscriber MUST be permitted to watch any Show that is not in early access.
permit (
    principal is Subscriber,
    action == Action::"watch",
    resource is Show
)
when {
    !resource.isEarlyAccess
};
