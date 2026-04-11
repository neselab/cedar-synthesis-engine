// Floor: any FreeMember MUST be permitted to watch any Show that is free.
permit (
    principal is FreeMember,
    action == Action::"watch",
    resource is Show
)
when {
    resource.isFree
};
