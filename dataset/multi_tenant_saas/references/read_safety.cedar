// Ceiling: readResource is permitted only when (principal is in the
// resource's tenant) OR (principal is global support AND support
// session is active AND ticketId is non-empty).
permit (
    principal is User,
    action == Action::"readResource",
    resource is Resource
)
when {
    principal.tenant == resource.tenant
    || (
        principal.isGlobalSupport
        && context.supportSessionActive
        && context.ticketId != ""
    )
};
